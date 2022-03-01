from datetime import timedelta
from unittest import mock

import pytest
from django.test import TestCase
from django.utils import timezone
from flag_engine.django_transform.document_builders import (
    build_environment_api_key_document,
)

from environments.identities.models import Identity
from environments.models import Environment, EnvironmentAPIKey
from features.models import Feature, FeatureState
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
class EnvironmentTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(
            name="Test Project", organisation=self.organisation
        )
        self.feature = Feature.objects.create(name="Test Feature", project=self.project)
        # The environment is initialised in a non-saved state as we want to test the save
        # functionality.
        self.environment = Environment(name="Test Environment", project=self.project)

    def test_environment_should_be_created_with_feature_states(self):
        # Given - set up data

        # When
        self.environment.save()

        # Then
        feature_states = FeatureState.objects.filter(environment=self.environment)
        assert hasattr(self.environment, "api_key")
        assert feature_states.count() == 1

    def test_on_creation_save_feature_states_get_created(self):
        # These should be no feature states before saving
        self.assertEqual(FeatureState.objects.count(), 0)

        self.environment.save()

        # On the first save a new feature state should be created
        self.assertEqual(FeatureState.objects.count(), 1)

    def test_on_update_save_feature_states_get_updated_not_created(self):
        self.environment.save()

        self.feature.default_enabled = True
        self.feature.save()
        self.environment.save()

        self.assertEqual(FeatureState.objects.count(), 1)

    def test_on_creation_save_feature_is_created_with_the_correct_default(self):
        self.environment.save()
        self.assertFalse(FeatureState.objects.get().enabled)

    def test_clone_does_not_modify_the_original_instance(self):
        # Given
        self.environment.save()

        # When
        clone = self.environment.clone(name="Cloned env")

        # Then
        self.assertNotEqual(clone.name, self.environment.name)
        self.assertNotEqual(clone.api_key, self.environment.api_key)

    def test_clone_save_creates_feature_states(self):
        # Given
        self.environment.save()

        # When
        clone = self.environment.clone(name="Cloned env")

        # Then
        feature_states = FeatureState.objects.filter(environment=clone)
        assert feature_states.count() == 1

    def test_clone_does_not_modify_source_feature_state(self):
        # Given
        self.environment.save()
        source_feature_state_before_clone = FeatureState.objects.filter(
            environment=self.environment
        ).first()

        # When
        self.environment.clone(name="Cloned env")
        source_feature_state_after_clone = FeatureState.objects.filter(
            environment=self.environment
        ).first()

        # Then
        assert source_feature_state_before_clone == source_feature_state_after_clone

    def test_clone_does_not_create_identity(self):
        # Given
        self.environment.save()
        Identity.objects.create(
            environment=self.environment, identifier="test_identity"
        )
        # When
        clone = self.environment.clone(name="Cloned env")

        # Then
        assert clone.identities.count() == 0

    def test_clone_clones_the_feature_states(self):
        # Given
        self.environment.save()

        # Enable the feature in the source environment
        self.environment.feature_states.update(enabled=True)

        # When
        clone = self.environment.clone(name="Cloned env")

        # Then
        assert clone.feature_states.first().enabled is True

    @mock.patch("environments.models.environment_cache")
    def test_get_from_cache_stores_environment_in_cache_on_success(self, mock_cache):
        # Given
        self.environment.save()
        mock_cache.get.return_value = None

        # When
        environment = Environment.get_from_cache(self.environment.api_key)

        # Then
        assert environment == self.environment
        mock_cache.set.assert_called_with(
            self.environment.api_key, self.environment, timeout=60
        )

    def test_get_from_cache_returns_None_if_no_matching_environment(self):
        # Given
        api_key = "no-matching-env"

        # When
        env = Environment.get_from_cache(api_key)

        # Then
        assert env is None

    def test_get_from_cache_accepts_environment_api_key_model_key(self):
        # Given
        self.environment.save()
        api_key = EnvironmentAPIKey.objects.create(
            name="Some key", environment=self.environment
        )

        # When
        environment_from_cache = Environment.get_from_cache(api_key=api_key.key)

        # Then
        assert environment_from_cache == self.environment

    def test_get_from_cache_with_null_environment_key_returns_null(self):
        # Given
        self.environment.save()

        # When
        environment = Environment.get_from_cache(None)

        # Then
        assert environment is None


def test_saving_environment_api_key_calls_put_item_with_correct_arguments(
    environment, mocker
):
    # Given
    mocked_dynamo_api_key_table = mocker.patch(
        "environments.models.dynamo_api_key_table"
    )
    # When
    api_key = EnvironmentAPIKey.objects.create(name="Some key", environment=environment)

    # Then
    mocked_dynamo_api_key_table.put_item.assert_called_with(
        Item=build_environment_api_key_document(api_key)
    )


def test_environment_api_key_model_is_valid_is_true_for_non_expired_active_key(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment,
            key="ser.random_key",
            name="test_key",
        ).is_valid
        is True
    )


def test_environment_api_key_model_is_valid_is_true_for_non_expired_active_key_with_expired_date_in_future(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment,
            key="ser.random_key",
            name="test_key",
            expires_at=timezone.now() + timedelta(days=5),
        ).is_valid
        is True
    )


def test_environment_api_key_model_is_valid_is_false_for_expired_active_key(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment,
            key="ser.random_key",
            name="test_key",
            expires_at=timezone.now() - timedelta(seconds=1),
        ).is_valid
        is False
    )


def test_environment_api_key_model_is_valid_is_false_for_non_expired_inactive_key(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment, key="ser.random_key", name="test_key", active=False
        ).is_valid
        is False
    )


def test_existence_of_multiple_environment_api_keys_does_not_break_get_from_cache(
    environment,
):
    # Given
    environment_api_keys = [
        EnvironmentAPIKey.objects.create(environment=environment, name=f"test_key_{i}")
        for i in range(2)
    ]

    # When
    retrieved_environments = [
        Environment.get_from_cache(environment.api_key),
        *[
            Environment.get_from_cache(environment_api_key.key)
            for environment_api_key in environment_api_keys
        ],
    ]

    # Then
    assert all(
        retrieved_environment == environment
        for retrieved_environment in retrieved_environments
    )
