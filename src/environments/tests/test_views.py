from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from environments.models import Environment, Identity, Trait
from features.models import Feature, FeatureState, FeatureSegment
from organisations.models import Organisation
from projects.models import Project
from segments import models
from segments.models import Segment, SegmentRule, Condition
from util.tests import Helper


@pytest.mark.django_db
class EnvironmentTestCase(TestCase):
    env_post_template_wout_webhook = '{"name": "%s", "project": %d}'
    env_post_template_with_webhook = '{"name": "%s", "project": %d, ' \
                                     '"webhooks_enabled": "%r", "webhook_url": "%s"}'
    fs_put_template = '{ "id" : %d, "enabled" : "%r", "feature_state_value" : "%s" }'

    def set_up(self):
        client = APIClient()
        user = Helper.create_ffadminuser()
        client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name='ssg')
        user.organisations.add(self.organisation)

        self.project = Project.objects.create(name='Test project', organisation=self.organisation)

        return client

    def test_should_create_environments_with_or_without_webhooks(self):
        # Given
        client = self.set_up()

        # When
        response_with_webhook = client.post('/api/v1/environments/',
                                            data=self.env_post_template_with_webhook % (
                                                "Test Env with Webhooks",
                                                self.project.id,
                                                True,
                                                "https://sometesturl.org"
                                            ), content_type="application/json")

        response_wout_webhook = client.post('/api/v1/environments/',
                                            data=self.env_post_template_wout_webhook % (
                                                "Test Env without Webhooks",
                                                self.project.id
                                            ), content_type="application/json")

        # Then
        assert response_with_webhook.status_code == status.HTTP_201_CREATED
        assert Environment.objects.get(name="Test Env with Webhooks").webhook_url
        assert response_wout_webhook.status_code == status.HTTP_201_CREATED

    def test_should_return_identities_for_an_environment(self):
        client = self.set_up()

        # Given
        identifierOne = 'user1'
        identifierTwo = 'user2'
        project = Project(name='project1', organisation=self.organisation)
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
        feature = Feature(name="feature", project=self.project)
        feature.save()
        environment = Environment.objects.create(name="test env", project=self.project)
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


@pytest.mark.django_db
class IdentityTestCase(TestCase):
    identifier = 'user1'
    put_template = '{ "enabled" : "%r" }'
    post_template = '{ "feature" : "%s", "enabled" : "%r" }'
    feature_states_url = '/api/v1/environments/%s/identities/%s/featurestates/'
    feature_states_detail_url = feature_states_url + "%d/"
    identities_url = '/api/v1/environments/%s/identities/%s/'

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name='Test Org')
        user.organisations.add(self.organisation)

        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test Environment', project=self.project)
        self.identity = Identity.objects.create(identifier=self.identifier, environment=self.environment)

    def tearDown(self) -> None:
        Helper.clean_up()

    def test_should_return_identities_list_when_requested(self):
        # Given - set up data

        # When
        response = self.client.get(self.identities_url % (self.identity.environment.api_key,
                                                          self.identity.id))

        # Then
        assert response.status_code == status.HTTP_200_OK

    def test_should_create_identity_feature_when_post(self):
        # Given
        feature = Feature.objects.create(name='feature1', project=self.project)

        # When
        response = self.client.post(self.feature_states_url % (self.identity.environment.api_key,
                                                               self.identity.id),
                                    data=self.post_template % (feature.id, True),
                                    content_type='application/json')

        # Then
        identity_features = self.identity.identity_features
        assert response.status_code == status.HTTP_201_CREATED
        assert identity_features.count() == 1

    def test_should_return_BadRequest_when_duplicate_identityFeature_is_posted(self):
        # Given
        feature = Feature.objects.create(name='feature2', project=self.project)

        # When
        initial_response = self.client.post(self.feature_states_url % (self.identity.environment.api_key,
                                                                       self.identity.id),
                                            data=self.post_template % (feature.id, True),
                                            content_type='application/json')
        second_response = self.client.post(self.feature_states_url % (self.identity.environment.api_key,
                                                                      self.identity.id),
                                           data=self.post_template % (feature.id, True),
                                           content_type='application/json')

        # Then
        identity_feature = self.identity.identity_features
        assert initial_response.status_code == status.HTTP_201_CREATED
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST
        assert identity_feature.count() == 1

    def test_should_change_enabled_state_when_put(self):
        # Given
        feature = Feature.objects.create(name='feature1', project=self.project)
        feature_state = FeatureState.objects.create(feature=feature,
                                                    identity=self.identity,
                                                    enabled=False,
                                                    environment=self.environment)

        # When
        response = self.client.put(self.feature_states_detail_url % (self.identity.environment.api_key,
                                                                     self.identity.id,
                                                                     feature_state.id),
                                   data=self.put_template % True,
                                   content_type='application/json')
        feature_state.refresh_from_db()

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert feature_state.enabled == True

    def test_should_remove_identity_feature_when_delete(self):
        # Given
        feature_one = Feature.objects.create(name='feature1', project=self.project)
        feature_two = Feature.objects.create(name='feature2', project=self.project)
        identity_feature_one = FeatureState.objects.create(feature=feature_one,
                                                           identity=self.identity,
                                                           enabled=False,
                                                           environment=self.environment)
        identity_feature_two = FeatureState.objects.create(feature=feature_two,
                                                           identity=self.identity,
                                                           enabled=True,
                                                           environment=self.environment)

        # When
        self.client.delete(self.feature_states_detail_url % (self.identity.environment.api_key,
                                                             self.identity.id,
                                                             identity_feature_one.id),
                           content_type='application/json')

        # Then
        identity_features = FeatureState.objects.filter(identity=self.identity)
        assert identity_features.count() == 1


@pytest.mark.django_db
class SDKIdentitiesTestCase(APITestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test Org')
        self.project = Project.objects.create(organisation=self.organisation, name='Test Project')
        self.environment = Environment.objects.create(project=self.project, name='Test Environment')
        self.feature_1 = Feature.objects.create(project=self.project, name='Test Feature 1')
        self.feature_2 = Feature.objects.create(project=self.project, name='Test Feature 2')
        self.identity = Identity.objects.create(environment=self.environment, identifier='test-identity')

    def tearDown(self) -> None:
        Segment.objects.all().delete()

    def test_identities_endpoint_returns_all_feature_states_for_identity_if_feature_not_provided(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert len(response.json().get('flags')) == 2

    def test_identities_endpoint_returns_traits(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier
        trait = Trait.objects.create(identity=self.identity, trait_key='trait_key', value_type='STRING',
                                     string_value='trait_value')

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert response.json().get('traits') is not None

        # and
        assert response.json().get('traits')[0].get('trait_value') == trait.get_trait_value()

    def test_identities_endpoint_returns_single_feature_state_if_feature_provided(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier + '&feature=' + self.feature_1.name

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert response.json().get('feature').get('name') == self.feature_1.name

    def test_identities_endpoint_returns_value_for_segment_if_identity_in_segment(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier

        trait_key = 'trait_key'
        trait_value = 'trait_value'
        Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type='STRING', string_value=trait_value)
        segment = Segment.objects.create(name='Test Segment', project=self.project)
        segment_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(operator='EQUAL', property=trait_key, value=trait_value, rule=segment_rule)
        FeatureSegment.objects.create(segment=segment, feature=self.feature_2, enabled=True, priority=1)

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert response.json().get('flags')[1].get('enabled')

    def test_identities_endpoint_returns_value_for_segment_if_identity_in_segment_and_feature_specified(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier + '&feature=' + self.feature_1.name

        trait_key = 'trait_key'
        trait_value = 'trait_value'
        Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type='STRING',
                             string_value=trait_value)
        segment = Segment.objects.create(name='Test Segment', project=self.project)
        segment_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
        Condition.objects.create(operator='EQUAL', property=trait_key, value=trait_value, rule=segment_rule)
        FeatureSegment.objects.create(segment=segment, feature=self.feature_1, enabled=True, priority=1)

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # and
        assert response.json().get('enabled')

    def test_identities_endpoint_returns_value_for_segment_if_rule_type_percentage_split_and_identity_in_segment(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier

        segment = Segment.objects.create(name='Test Segment', project=self.project)
        segment_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

        identity_percentage_value = segment.get_identity_percentage_value(self.identity)
        Condition.objects.create(operator=models.PERCENTAGE_SPLIT,
                                 value=identity_percentage_value + (1 - identity_percentage_value) / 2,
                                 rule=segment_rule)
        FeatureSegment.objects.create(segment=segment, feature=self.feature_1, enabled=True, priority=1)

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert response.json().get('flags')[0].get('enabled')

    def test_identities_endpoint_returns_default_value_if_rule_type_percentage_split_and_identity_not_in_segment(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier

        segment = Segment.objects.create(name='Test Segment', project=self.project)
        segment_rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)

        identity_percentage_value = segment.get_identity_percentage_value(self.identity)
        Condition.objects.create(operator=models.PERCENTAGE_SPLIT,
                                 value=identity_percentage_value / 2,
                                 rule=segment_rule)
        FeatureSegment.objects.create(segment=segment, feature=self.feature_1, enabled=True, priority=1)

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        assert not response.json().get('flags')[0].get('enabled')
