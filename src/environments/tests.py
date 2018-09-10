from django.test import TestCase

from .models import Environment, Identity
from features.models import Feature, FeatureState
from organisations.models import Organisation
from projects.models import Project


class EnvironmentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organisation = Organisation.objects.create(name="Test Org")
        cls.project = Project.objects.create(name="Test Project", organisation=cls.organisation)
        cls.feature = Feature.objects.create(name="Test Feature", project=cls.project)
        cls.environment = Environment.objects.create(name="Test Environment", project=cls.project)

    def test_environment_should_be_created_with_feature_states(self):
        feature_states = FeatureState.objects.filter(environment=self.environment)

        self.assertTrue(hasattr(self.environment, 'api_key'))
        self.assertEquals(feature_states.count(), 1)


class EnvironmentSaveTestCase(TestCase):
    def setUp(self):
        self.organisation = Organisation.objects.create(name="Test Org")
        self.project = Project.objects.create(name="Test Project", organisation=self.organisation)
        self.feature = Feature.objects.create(name="Test Feature", project=self.project)
        # The environment is initialised in a non-saved state as we want to test the save
        # functionality.
        self.environment = Environment(name="Test Environment", project=self.project)

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

        self.environment.save()
        self.assertTrue(FeatureState.objects.get().enabled)

    def test_on_update_save_feature_states_dont_get_updated_if_identity_present(self):
        self.environment.save()
        identity = Identity.objects.create(identifier="test-identity", environment=self.environment)

        fs = FeatureState.objects.get()
        fs.id = None
        fs.identity = identity
        fs.save()
        self.assertEqual(FeatureState.objects.count(), 2)

        self.feature.default_enabled = True
        self.feature.save()
        self.environment.save()
        fs.refresh_from_db()

        self.assertNotEqual(fs.enabled, FeatureState.objects.exclude(id=fs.id).get().enabled)


class IdentityTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organisation = Organisation.objects.create(name="Test Org")
        cls.project = Project.objects.create(name="Test Project", organisation=cls.organisation)
        cls.environment = Environment.objects.create(name="Test Environment", project=cls.project)

    def test_create_identity_should_assign_relevant_attributes(self):
        identity = Identity.objects.create(identifier="test-identity", environment=self.environment)

        self.assertIsInstance(identity.environment, Environment)
        self.assertTrue(hasattr(identity, 'created_date'))

    def test_get_all_feature_states(self):
        feature = Feature.objects.create(name="Test Feature", project=self.project)
        feature_2 = Feature.objects.create(name="Test Feature 2", project=self.project)
        environment_2 = Environment.objects.create(name="Test Environment 2", project=self.project)

        identity_1 = Identity.objects.create(
            identifier="test-identity-1",
            environment=self.environment,
        )
        identity_2 = Identity.objects.create(
            identifier="test-identity-2",
            environment=self.environment,
        )
        identity_3 = Identity.objects.create(
            identifier="test-identity-3",
            environment=environment_2,
        )

        # User unassigned - automatically should be created via `Feature` save method.
        fs_environment_anticipated = FeatureState.objects.get(
            feature=feature_2,
            environment=self.environment,
        )

        # User assigned
        fs_identity_anticipated = FeatureState.objects.create(
            feature=feature,
            environment=self.environment,
            identity=identity_1,
        )
        FeatureState.objects.create(
            feature=feature,
            environment=self.environment,
            identity=identity_2,
        )
        FeatureState.objects.create(
            feature=feature,
            environment=environment_2,
            identity=identity_3,
        )

        # For identity_1 all items in a different environment should not appear. Identity
        # specific flags should be returned as well as non-identity specific ones that have not
        # already been returned via the identity specific result.
        flags = identity_1.get_all_feature_states()
        self.assertEqual(len(flags), 2)
        self.assertIn(fs_environment_anticipated, flags)
        self.assertIn(fs_identity_anticipated, flags)
