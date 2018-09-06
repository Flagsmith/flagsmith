from unittest import mock

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
        FeatureState.objects.get(
            feature=feature,
            environment=self.environment,
        )
        fs_environment_anticipated = FeatureState.objects.get(
            feature=feature_2,
            environment=self.environment,
        )
        FeatureState.objects.get(
            feature=feature,
            environment=environment_2,
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
