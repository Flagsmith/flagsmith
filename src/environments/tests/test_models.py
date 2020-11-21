import pytest
from django.test import TestCase

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature, FeatureState
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.django_db
class EnvironmentSaveTestCase(TestCase):
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

    def test_on_update_save_feature_gets_updated_with_the_correct_default(self):
        self.environment.save()
        self.assertFalse(FeatureState.objects.get().enabled)

        self.feature.default_enabled = True
        self.feature.save()

        self.assertTrue(FeatureState.objects.get().enabled)

    def test_on_update_save_feature_states_dont_get_updated_if_identity_present(self):
        self.environment.save()
        identity = Identity.objects.create(
            identifier="test-identity", environment=self.environment
        )

        fs = FeatureState.objects.get()
        fs.id = None
        fs.identity = identity
        fs.save()
        self.assertEqual(FeatureState.objects.count(), 2)

        self.feature.default_enabled = True
        self.feature.save()
        self.environment.save()
        fs.refresh_from_db()

        self.assertNotEqual(
            fs.enabled, FeatureState.objects.exclude(id=fs.id).get().enabled
        )
