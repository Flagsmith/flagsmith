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


