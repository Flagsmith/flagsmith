from unittest import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment, Identity
from features.models import Feature, FeatureState
from organisations.models import Organisation
from projects.models import Project
from util.tests import Helper


class EnvironmentTestCase(TestCase):
    env_post_template_wout_webhook = '{"name": %s, "project": %d}'
    env_post_template_with_webhook = '{"name": "%s", "project": %d, ' \
                                     '"webhooks_enabled": "%r", "webhook_url": "%s"}'
    fs_put_template = '{ "id" : %d, "enabled" : "%r", "feature_state_value" : "%s" }'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_create_environments_with_or_without_webhooks(self):
        # Given
        client = self.set_up()

        # When
        response_with_webhook = client.post('/api/v1/environments/',
                                            data=self.env_post_template_with_webhook % (
                                                "Test Env with Webhooks",
                                                1,
                                                True,
                                                "https://sometesturl.org"
                                            ), content_type="application/json")

        response_wout_webhook = client.post('/api/v1/environments/',
                                            data=self.env_post_template_wout_webhook % (
                                                "Test Env without Webhooks",
                                                1
                                            ), content_type="application/json")

        # Then
        self.assertTrue(response_with_webhook.status_code, 201)
        self.assertTrue(Environment.objects.get(name="Test Env with Webhooks").webhook_url)
        self.assertTrue(response_wout_webhook.status_code, 201)

    def test_should_return_identities_for_an_environment(self):
        client = self.set_up()

        # Given
        identifierOne = 'user1'
        identifierTwo = 'user2'
        organisation = Organisation(name='ssg')
        organisation.save()
        project = Project(name='project1', organisation=organisation)
        project.save()
        environment = Environment(name='environment1', project=project)
        environment.save()
        identityOne = Identity(identifier=identifierOne, environment=environment)
        identityOne.save()
        identityTwo = Identity(identifier=identifierTwo, environment=environment)
        identityTwo.save()
        # When
        response = client.get('/api/v1/environments/%s/identities/' % environment.api_key)
        # Then
        self.assertEquals(response.data['results'][0]['identifier'], identifierOne)
        self.assertEquals(response.data['results'][1]['identifier'], identifierTwo)

    def test_should_update_value_of_feature_state(self):
        # Given
        client = self.set_up()
        project = Project.objects.get(name="test project")
        feature = Feature(name="feature", project=project)
        feature.save()
        environment = Environment.objects.get(name="test env")
        feature_state = FeatureState.objects.get(feature=feature, environment=environment)

        # When
        response = client.put("/api/v1/environments/%s/featurestates/%d/" %
                              (environment.api_key, feature_state.id),
                              data=self.fs_put_template % (feature_state.id,
                                                           True,
                                                           "This is a value"),
                              content_type='application/json')  # should change enabled to True

        # Then
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        feature_state.refresh_from_db()
        self.assertEquals(feature_state.get_feature_state_value(), "This is a value")
        self.assertEquals(feature_state.enabled, True)

        Helper.clean_up()


class IdentityTestCase(TestCase):
    identifier = 'user1'
    put_template = '{ "enabled" : "%r" }'
    post_template = '{ "feature" : "%s", "enabled" : "%r" }'
    feature_states_url = '/api/v1/environments/%s/identities/%s/featurestates/'
    feature_states_detail_url = feature_states_url + "%d/"
    identities_url = '/api/v1/environments/%s/identities/%s/'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)
        return client

    def test_should_return_identities_list_when_requested(self):
        # Given
        client = self.set_up()
        identity, project = Helper.generate_database_models(identifier=self.identifier)
        # When
        response = client.get(self.identities_url % (identity.environment.api_key,
                                                     identity.identifier))
        # Then
        self.assertEquals(response.status_code, 200)
        Helper.clean_up()

    def test_should_create_identityFeature_when_post(self):
        # Given
        client = self.set_up()
        environment = Environment.objects.get(name="test env")
        identity = Identity.objects.create(environment=environment, identifier="testidentity")
        project = Project.objects.get(name="test project")
        feature = Feature(name='feature1', project=project)
        feature.save()
        # When
        response = client.post(self.feature_states_url % (identity.environment.api_key,
                                                          identity.identifier),
                               data=self.post_template % (feature.id, True),
                               content_type='application/json')
        # Then
        identityFeature = identity.identity_features
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(identityFeature.count(), 1)
        Helper.clean_up()

    def test_should_return_BadRequest_when_duplicate_identityFeature_is_posted(self):
        # Given
        client = self.set_up()
        identity, project = Helper.generate_database_models(self.identifier)
        feature = Feature(name='feature2', project=project)
        feature.save()
        # When
        initialResponse = client.post(self.feature_states_url % (identity.environment.api_key,
                                                                 identity.identifier),
                                      data=self.post_template % (feature.id, True),
                                      content_type='application/json')
        secondResponse = client.post(self.feature_states_url % (identity.environment.api_key,
                                                                identity.identifier),
                                     data=self.post_template % (feature.id, True),
                                     content_type='application/json')
        # Then
        identityFeature = identity.identity_features
        self.assertEquals(initialResponse.status_code, status.HTTP_201_CREATED)
        self.assertEquals(secondResponse.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(identityFeature.count(), 1)
        Helper.clean_up()

    def test_should_change_enabled_state_when_put(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        project = Project.objects.get(name="test project", organisation=organisation)
        feature = Feature(name='feature1', project=project)
        feature.save()
        environment = Environment.objects.get(name="test env")
        identity = Identity(identifier="test_identity", environment=environment)
        identity.save()
        feature_state = FeatureState(feature=feature,
                                     identity=identity,
                                     enabled=False,
                                     environment=environment)
        feature_state.save()
        # When
        response = client.put(self.feature_states_detail_url % (identity.environment.api_key,
                                                                identity.identifier,
                                                                feature_state.id),
                              data=self.put_template % True,
                              content_type='application/json')
        feature_state.refresh_from_db()
        # Then
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(feature_state.enabled, True)
        Helper.clean_up()

    def test_should_remove_identityfeature_when_delete(self):
        # Given
        client = self.set_up()
        organisation = Organisation.objects.get(name="test org")
        project = Project.objects.get(name="test project", organisation=organisation)
        feature_one = Feature(name='feature1', project=project)
        feature_one.save()
        feature_two = Feature(name='feature2', project=project)
        feature_two.save()
        environment = Environment.objects.get(name="test env")
        identity = Identity(identifier="test_identity", environment=environment)
        identity.save()
        environment = Environment.objects.get(name="test env")
        identity_feature_one = FeatureState(feature=feature_one,
                                            identity=identity,
                                            enabled=False,
                                            environment=environment)
        identity_feature_one.save()
        identity_feature_two = FeatureState(feature=feature_two,
                                            identity=identity,
                                            enabled=True,
                                            environment=environment)
        identity_feature_two.save()
        # When
        client.delete(self.feature_states_detail_url % (identity.environment.api_key,
                                                        identity.identifier,
                                                        identity_feature_one.id),
                      content_type='application/json')
        # Then
        identity_features = FeatureState.objects.filter(identity=identity)
        self.assertEquals(identity_features.count(), 1)
        Helper.clean_up()