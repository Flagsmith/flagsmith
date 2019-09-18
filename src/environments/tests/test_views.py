import json
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from audit.models import AuditLog, RelatedObjectType
from environments.models import Environment, Identity, Trait, INTEGER, STRING
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

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name='ssg')
        user.organisations.add(self.organisation)

        self.project = Project.objects.create(name='Test project', organisation=self.organisation)

    def tearDown(self) -> None:
        Environment.objects.all().delete()
        AuditLog.objects.all().delete()

    def test_should_create_environments_with_or_without_webhooks(self):
        # Given
        url = reverse('api:v1:environments:environment-list')

        # When
        response_with_webhook = self.client.post(url,
                                                 data=self.env_post_template_with_webhook % (
                                                     "Test Env with Webhooks",
                                                     self.project.id,
                                                     True,
                                                     "https://sometesturl.org"
                                                 ), content_type="application/json")

        response_wout_webhook = self.client.post('/api/v1/environments/',
                                                 data=self.env_post_template_wout_webhook % (
                                                     "Test Env without Webhooks",
                                                     self.project.id
                                                 ), content_type="application/json")

        # Then
        assert response_with_webhook.status_code == status.HTTP_201_CREATED
        assert Environment.objects.get(name="Test Env with Webhooks").webhook_url
        assert response_wout_webhook.status_code == status.HTTP_201_CREATED

    def test_should_return_identities_for_an_environment(self):
        # Given
        identifier_one = 'user1'
        identifier_two = 'user2'
        environment = Environment.objects.create(name='environment1', project=self.project)
        Identity.objects.create(identifier=identifier_one, environment=environment)
        Identity.objects.create(identifier=identifier_two, environment=environment)
        url = reverse('api:v1:environments:environment-identities-list', args=[environment.api_key])

        # When
        response = self.client.get(url)

        # Then
        assert response.data['results'][0]['identifier'] == identifier_one
        assert response.data['results'][1]['identifier'] == identifier_two

    def test_should_update_value_of_feature_state(self):
        # Given
        feature = Feature.objects.create(name="feature", project=self.project)
        environment = Environment.objects.create(name="test env", project=self.project)
        feature_state = FeatureState.objects.get(feature=feature, environment=environment)
        url = reverse('api:v1:environments:environment-featurestates-detail',
                      args=[environment.api_key, feature_state.id])

        # When
        response = self.client.put(url, data=self.fs_put_template % (feature_state.id, True, "This is a value"),
                                   content_type='application/json')

        # Then
        feature_state.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert feature_state.get_feature_state_value() == "This is a value"
        assert feature_state.enabled

    def test_audit_log_entry_created_when_new_environment_created(self):
        # Given
        url = reverse('api:v1:environments:environment-list')
        data = {
            'project': self.project.id,
            'name': 'Test Environment'
        }

        # When
        self.client.post(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.ENVIRONMENT.name).count() == 1

    def test_audit_log_entry_created_when_environment_updated(self):
        # Given
        environment = Environment.objects.create(name='Test environment', project=self.project)
        url = reverse('api:v1:environments:environment-detail', args=[environment.api_key])
        data = {
            'project': self.project.id,
            'name': 'New name'
        }

        # When
        self.client.put(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.ENVIRONMENT.name).count() == 1

    def test_audit_log_created_when_feature_state_updated(self):
        # Given
        feature = Feature.objects.create(name="feature", project=self.project)
        environment = Environment.objects.create(name="test env", project=self.project)
        feature_state = FeatureState.objects.get(feature=feature, environment=environment)
        url = reverse('api:v1:environments:environment-featurestates-detail',
                      args=[environment.api_key, feature_state.id])
        data = {
            'id': feature.id,
            'enabled': True
        }

        # When
        self.client.put(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE_STATE.name).count() == 1

        # and
        assert AuditLog.objects.first().author


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

    def test_can_search_for_identities(self):
        # Given
        Identity.objects.create(identifier='user2', environment=self.environment)
        base_url = reverse('api:v1:environments:environment-identities-list', args=[self.environment.api_key])
        url = '%s?q=%s' % (base_url, self.identifier)

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and - only identity matching search appears
        assert res.json().get('count') == 1

    def test_search_is_case_insensitive(self):
        # Given
        Identity.objects.create(identifier='user2', environment=self.environment)
        base_url = reverse('api:v1:environments:environment-identities-list', args=[self.environment.api_key])
        url = '%s?q=%s' % (base_url, self.identifier.upper())

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and - identity matching search appears
        assert res.json().get('count') == 1

    def test_no_identities_returned_if_search_matches_none(self):
        # Given
        base_url = reverse('api:v1:environments:environment-identities-list', args=[self.environment.api_key])
        url = '%s?q=%s' % (base_url, 'some invalid search string')

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert res.json().get('count') == 0

    def test_search_identities_still_allows_paging(self):
        # Given
        self._create_n_identities(10)
        base_url = reverse('api:v1:environments:environment-identities-list', args=[self.environment.api_key])
        url = '%s?q=%s' % (base_url, 'user')

        res1 = self.client.get(url)
        second_page = res1.json().get('next')

        # When
        res2 = self.client.get(second_page)

        # Then
        assert res2.status_code == status.HTTP_200_OK

        # and
        assert res2.json().get('results')

    def _create_n_identities(self, n):
        for i in range(2, n + 2):
            identifier = 'user%d' % i
            Identity.objects.create(identifier=identifier, environment=self.environment)

    def test_can_delete_identity(self):
        # Given
        url = reverse('api:v1:environments:environment-identities-detail', args=[self.environment.api_key,
                                                                                 self.identity.id])

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert not Identity.objects.filter(id=self.identity.id).exists()


@pytest.mark.django_db
class SDKIdentitiesTestCase(APITestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test Org')
        self.project = Project.objects.create(organisation=self.organisation, name='Test Project')
        self.environment = Environment.objects.create(project=self.project, name='Test Environment')
        self.feature_1 = Feature.objects.create(project=self.project, name='Test Feature 1')
        self.feature_2 = Feature.objects.create(project=self.project, name='Test Feature 2')
        self.identity = Identity.objects.create(environment=self.environment, identifier='test-identity')
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)

    def tearDown(self) -> None:
        Segment.objects.all().delete()

    def test_identities_endpoint_returns_all_feature_states_for_identity_if_feature_not_provided(self):
        # Given
        base_url = reverse('api:v1:sdk-identities')
        url = base_url + '?identifier=' + self.identity.identifier

        # When
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
                                 value=(identity_percentage_value + (1 - identity_percentage_value) / 2) * 100.0,
                                 rule=segment_rule)
        FeatureSegment.objects.create(segment=segment, feature=self.feature_1, enabled=True, priority=1)

        # When
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        response = self.client.get(url)

        # Then
        for flag in response.json()['flags']:
            if flag['feature']['name'] == self.feature_1.name:
                assert flag['enabled']

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


class SDKTraitsTest(APITestCase):
    JSON = 'application/json'

    def setUp(self) -> None:
        organisation = Organisation.objects.create(name='Test organisation')
        project = Project.objects.create(name='Test project', organisation=organisation)
        self.environment = Environment.objects.create(name='Test environment', project=project)
        self.identity = Identity.objects.create(identifier='test-user', environment=self.environment)
        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)
        self.trait_key = 'trait_key'
        self.trait_value = 'trait_value'

    def tearDown(self) -> None:
        Trait.objects.all().delete()
        Identity.objects.all().delete()

    def test_can_set_trait_for_an_identity(self):
        # Given
        url = reverse('api:v1:sdk-traits-list')

        # When
        res = self.client.post(url, data=self._generate_json_trait_data(), content_type=self.JSON)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Trait.objects.filter(identity=self.identity, trait_key=self.trait_key).exists()

    def test_add_trait_creates_identity_if_it_doesnt_exist(self):
        # Given
        url = reverse('api:v1:sdk-traits-list')
        identifier = 'new-identity'

        # When
        res = self.client.post(url, data=self._generate_json_trait_data(identifier=identifier), content_type=self.JSON)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert Identity.objects.filter(identifier=identifier, environment=self.environment).exists()

        # and
        assert Trait.objects.filter(identity__identifier=identifier, trait_key=self.trait_key).exists()

    def test_trait_is_updated_if_already_exists(self):
        # Given
        url = reverse('api:v1:sdk-traits-list')
        trait = Trait.objects.create(trait_key=self.trait_key, value_type=STRING, string_value=self.trait_value,
                                     identity=self.identity)
        new_value = 'Some new value'

        # When
        self.client.post(url, data=self._generate_json_trait_data(trait_value=new_value), content_type=self.JSON)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == new_value

    def test_increment_value_increments_trait_value_if_value_positive_integer(self):
        # Given
        initial_value = 2
        increment_by = 2

        url = reverse('api:v1:sdk-traits-increment-value')
        trait = Trait.objects.create(identity=self.identity, trait_key=self.trait_key, value_type=INTEGER,
                                     integer_value=initial_value)
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': increment_by
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == initial_value + increment_by

    def test_increment_value_decrements_trait_value_if_value_negative_integer(self):
        # Given
        initial_value = 2
        increment_by = -2

        url = reverse('api:v1:sdk-traits-increment-value')
        trait = Trait.objects.create(identity=self.identity, trait_key=self.trait_key, value_type=INTEGER,
                                     integer_value=initial_value)
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': increment_by
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait.refresh_from_db()
        assert trait.get_trait_value() == initial_value + increment_by

    def test_increment_value_initialises_trait_with_a_value_of_zero_if_it_doesnt_exist(self):
        # Given
        increment_by = 1

        url = reverse('api:v1:sdk-traits-increment-value')
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': increment_by
        }

        # When
        self.client.post(url, data=data)

        # Then
        trait = Trait.objects.get(trait_key=self.trait_key, identity=self.identity)
        assert trait.get_trait_value() == increment_by

    def test_increment_value_returns_400_if_trait_value_not_integer(self):
        # Given
        url = reverse('api:v1:sdk-traits-increment-value')
        Trait.objects.create(identity=self.identity, trait_key=self.trait_key, value_type=STRING, string_value='str')
        data = {
            'trait_key': self.trait_key,
            'identifier': self.identity.identifier,
            'increment_by': 2
        }

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def _generate_json_trait_data(self, identifier=None, trait_key=None, trait_value=None):
        if not identifier:
            identifier = self.identity.identifier

        if not trait_key:
            trait_key = self.trait_key

        if not trait_value:
            trait_value = self.trait_value

        return json.dumps({
            'identity': {
                'identifier': identifier
            },
            'trait_key': trait_key,
            'trait_value': trait_value
        })


@pytest.mark.django_db
class TraitViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name='Test org')
        user.organisations.add(organisation)

        self.project = Project.objects.create(name='Test project', organisation=organisation)
        self.environment = Environment.objects.create(name='Test environment', project=self.project)
        self.identity = Identity.objects.create(identifier='test-user', environment=self.environment)

    def test_can_delete_trait(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        url = reverse('api:v1:environments:identities-traits-detail',
                      args=[self.environment.api_key, self.identity.id, trait.id])

        # When
        res = self.client.delete(url)

        # Then
        assert res.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert not Trait.objects.filter(pk=trait.id).exists()

    def test_delete_trait_only_deletes_single_trait_if_query_param_not_provided(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        identity_2 = Identity.objects.create(identifier='test-user-2', environment=self.environment)

        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        trait_2 = Trait.objects.create(identity=identity_2, trait_key=trait_key, value_type=STRING,
                                       string_value=trait_value)

        url = reverse('api:v1:environments:identities-traits-detail',
                      args=[self.environment.api_key, self.identity.id, trait.id])

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert Trait.objects.filter(pk=trait_2.id).exists()

    def test_delete_trait_deletes_all_traits_if_query_param_provided(self):
        # Given
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        identity_2 = Identity.objects.create(identifier='test-user-2', environment=self.environment)

        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        trait_2 = Trait.objects.create(identity=identity_2, trait_key=trait_key, value_type=STRING,
                                       string_value=trait_value)

        base_url = reverse('api:v1:environments:identities-traits-detail',
                           args=[self.environment.api_key, self.identity.id, trait.id])
        url = base_url + '?deleteAllMatchingTraits=true'

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert not Trait.objects.filter(pk=trait_2.id).exists()

    def test_delete_trait_only_deletes_traits_in_current_environment(self):
        # Given
        environment_2 = Environment.objects.create(name='Test environment', project=self.project)
        trait_key = 'trait_key'
        trait_value = 'trait_value'
        identity_2 = Identity.objects.create(identifier='test-user-2', environment=environment_2)

        trait = Trait.objects.create(identity=self.identity, trait_key=trait_key, value_type=STRING,
                                     string_value=trait_value)
        trait_2 = Trait.objects.create(identity=identity_2, trait_key=trait_key, value_type=STRING,
                                       string_value=trait_value)

        base_url = reverse('api:v1:environments:identities-traits-detail',
                           args=[self.environment.api_key, self.identity.id, trait.id])
        url = base_url + '?deleteAllMatchingTraits=true'

        # When
        self.client.delete(url)

        # Then
        assert not Trait.objects.filter(pk=trait.id).exists()

        # and
        assert Trait.objects.filter(pk=trait_2.id).exists()
