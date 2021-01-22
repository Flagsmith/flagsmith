from unittest import mock

import pytest
from django.test import TestCase

from environments.identities.models import Identity
from environments.models import Environment
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
