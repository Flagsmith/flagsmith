import json
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from audit.models import AuditLog, RelatedObjectType, IDENTITY_FEATURE_STATE_UPDATED_MESSAGE, \
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE
from environments.models import Environment, Identity
from features.models import Feature, FeatureState, FeatureSegment, CONFIG, FeatureStateValue
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser
from util.tests import Helper


@pytest.mark.django_db
class ProjectFeatureTestCase(TestCase):
    project_features_url = '/api/v1/projects/%s/features/'
    project_feature_detail_url = '/api/v1/projects/%s/features/%d/'
    post_template = '{ "name": "%s", "project": %d, "initial_value": "%s" }'

    def setUp(self):
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        self.organisation = Organisation.objects.create(name='Test Org')

        user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment_1 = Environment.objects.create(name='Test environment 1', project=self.project)
        self.environment_2 = Environment.objects.create(name='Test environment 2', project=self.project)

    def test_should_create_feature_states_when_feature_created(self):
        # Given - set up data
        default_value = 'This is a value'

        # When
        response = self.client.post(self.project_features_url % self.project.id,
                                    data=self.post_template % ("test feature", self.project.id,
                                                               default_value),
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        # check feature was created successfully
        assert Feature.objects.filter(name="test feature", project=self.project.id).count() == 1

        # check feature was added to environment
        assert FeatureState.objects.filter(environment=self.environment_1).count() == 1
        assert FeatureState.objects.filter(environment=self.environment_2).count() == 1

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.filter(environment=self.environment_1).first()
        assert feature_state.get_feature_state_value() == default_value

    def test_should_create_feature_states_with_integer_value_when_feature_created(self):
        # Given - set up data
        default_value = 12

        # When
        response = self.client.post(self.project_features_url % self.project.id,
                                    data=self.post_template % ("test feature", self.project.id,
                                                               default_value),
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        # check feature was created successfully
        assert Feature.objects.filter(name="test feature", project=self.project.id).count() == 1

        # check feature was added to environment
        assert FeatureState.objects.filter(environment=self.environment_1).count() == 1
        assert FeatureState.objects.filter(environment=self.environment_2).count() == 1

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.filter(environment=self.environment_1).first()
        assert feature_state.get_feature_state_value() == default_value

    def test_should_create_feature_states_with_boolean_value_when_feature_created(self):
        # Given - set up data
        default_value = True
        feature_name = 'Test feature'
        data = {
            'name': 'Test feature',
            'project': self.project.id,
            'initial_value': default_value
        }

        # When
        response = self.client.post(self.project_features_url % self.project.id,
                                    data=json.dumps(data),
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        # check feature was created successfully
        assert Feature.objects.filter(name=feature_name, project=self.project.id).count() == 1

        # check feature was added to environment
        assert FeatureState.objects.filter(environment=self.environment_1).count() == 1
        assert FeatureState.objects.filter(environment=self.environment_2).count() == 1

        # check that value was correctly added to feature state
        feature_state = FeatureState.objects.filter(environment=self.environment_1).first()
        assert feature_state.get_feature_state_value() == default_value

    def test_should_delete_feature_states_when_feature_deleted(self):
        # Given
        feature = Feature.objects.create(name="test feature", project=self.project)

        # When
        response = self.client.delete(self.project_feature_detail_url % (self.project.id, feature.id))

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        # check feature was deleted succesfully
        assert Feature.objects.filter(name="test feature", project=self.project.id).count() == 0

        # check feature was removed from all environments
        assert FeatureState.objects.filter(environment=self.environment_1, feature=feature).count() == 0
        assert FeatureState.objects.filter(environment=self.environment_2, feature=feature).count() == 0

    def test_audit_log_created_when_feature_created(self):
        # Given
        url = reverse('api-v1:projects:project-features-list', args=[self.project.id])
        data = {
            'name': 'Test feature flag',
            'type': 'FLAG',
            'project': self.project.id
        }

        # When
        self.client.post(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE.name).count() == 1

    def test_audit_log_created_when_feature_updated(self):
        # Given
        feature = Feature.objects.create(name='Test Feature', project=self.project)
        url = reverse('api-v1:projects:project-features-detail', args=[self.project.id, feature.id])
        data = {
            'name': 'Test Feature updated',
            'type': 'FLAG',
            'project': self.project.id
        }

        # When
        self.client.put(url, data=data)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE.name).count() == 1

    def test_audit_log_created_when_feature_segments_updated(self):
        # Given
        segment = Segment.objects.create(name='Test segment', project=self.project)
        feature = Feature.objects.create(name='Test feature', project=self.project)
        url = reverse('api-v1:projects:project-features-segments', args=[self.project.id, feature.id])
        data = [{
            'segment': segment.id,
            'priority': 1,
            'enabled': True
        }]

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE.name).count() == 1

    def test_audit_log_created_when_feature_state_created_for_identity(self):
        # Given
        feature = Feature.objects.create(name='Test feature', project=self.project)
        identity = Identity.objects.create(identifier='test-identifier', environment=self.environment_1)
        url = reverse('api-v1:environments:identity-featurestates-list', args=[self.environment_1.api_key,
                                                                               identity.id])
        data = {
            "feature": feature.id,
            "enabled": True
        }

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE_STATE.name).count() == 1

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (feature.name, identity.identifier)
        audit_log = AuditLog.objects.get(related_object_type=RelatedObjectType.FEATURE_STATE.name)
        assert audit_log.log == expected_log_message

    def test_audit_log_created_when_feature_state_updated_for_identity(self):
        # Given
        feature = Feature.objects.create(name='Test feature', project=self.project)
        identity = Identity.objects.create(identifier='test-identifier', environment=self.environment_1)
        feature_state = FeatureState.objects.create(feature=feature, environment=self.environment_1, identity=identity,
                                                    enabled=True)
        url = reverse('api-v1:environments:identity-featurestates-detail', args=[self.environment_1.api_key,
                                                                                 identity.id, feature_state.id])
        data = {
            "feature": feature.id,
            "enabled": False
        }

        # When
        res = self.client.put(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE_STATE.name).count() == 1

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (feature.name, identity.identifier)
        audit_log = AuditLog.objects.get(related_object_type=RelatedObjectType.FEATURE_STATE.name)
        assert audit_log.log == expected_log_message

    def test_audit_log_created_when_feature_state_deleted_for_identity(self):
        # Given
        feature = Feature.objects.create(name='Test feature', project=self.project)
        identity = Identity.objects.create(identifier='test-identifier', environment=self.environment_1)
        feature_state = FeatureState.objects.create(feature=feature, environment=self.environment_1, identity=identity,
                                                    enabled=True)
        url = reverse('api-v1:environments:identity-featurestates-detail', args=[self.environment_1.api_key,
                                                                                 identity.id, feature_state.id])

        # When
        res = self.client.delete(url)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE_STATE.name).count() == 1

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_DELETED_MESSAGE % (feature.name, identity.identifier)
        audit_log = AuditLog.objects.get(related_object_type=RelatedObjectType.FEATURE_STATE.name)
        assert audit_log.log == expected_log_message


@pytest.mark.django_db
class FeatureSegmentViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name='Test Org')

        user.add_organisation(organisation, OrganisationRole.ADMIN)

        self.project = Project.objects.create(organisation=organisation, name='Test project')
        self.environment_1 = Environment.objects.create(project=self.project, name='Test environment 1')
        self.environment_2 = Environment.objects.create(project=self.project, name='Test environment 2')
        self.feature = Feature.objects.create(project=self.project, name='Test feature')
        self.segment = Segment.objects.create(project=self.project, name='Test segment')

    def test_when_feature_segments_updated_then_feature_states_updated_for_each_environment(self):
        # Given
        url = reverse('api-v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
        FeatureSegment.objects.create(segment=self.segment, feature=self.feature, enabled=False)
        data = [{
            'segment': self.segment.id,
            'priority': 1,
            'enabled': True
        }]

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        for env in Environment.objects.all():
            assert FeatureState.objects.get(environment=env, feature_segment__segment=self.segment).enabled

    def test_when_feature_segments_created_with_integer_value_then_feature_states_created_with_integer_value(self):
        # Given
        url = reverse('api-v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
        value = 1

        data = [{
            'segment': self.segment.id,
            'priority': 1,
            'value': value
        }]

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        for env in Environment.objects.all():
            fs = FeatureState.objects.get(environment=env, feature_segment__segment=self.segment)
            assert fs.get_feature_state_value() == value

    def test_when_feature_segments_created_with_boolean_value_then_feature_states_created_with_boolean_value(self):
        # Given
        url = reverse('api-v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
        value = False

        data = [{
            'segment': self.segment.id,
            'priority': 1,
            'value': value
        }]

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        for env in Environment.objects.all():
            fs = FeatureState.objects.get(environment=env, feature_segment__segment=self.segment)
            assert fs.get_feature_state_value() == value

    def test_when_feature_segments_created_with_string_value_then_feature_states_created_with_string_value(self):
        # Given
        url = reverse('api-v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
        value = 'my_string'

        data = [{
            'segment': self.segment.id,
            'priority': 1,
            'value': value
        }]

        # When
        self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        for env in Environment.objects.all():
            fs = FeatureState.objects.get(environment=env, feature_segment__segment=self.segment)
            assert fs.get_feature_state_value() == value


@pytest.mark.django_db()
class FeatureStateViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name='Test org')
        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment = Environment.objects.create(project=self.project, name='Test environment')
        self.feature = Feature.objects.create(name='test-feature', project=self.project, type='CONFIG',
                                              initial_value=12)
        self.user = FFAdminUser.objects.create(email='test@example.com')
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_update_feature_state_value_updates_feature_state_value(self):
        # Given
        feature_state = FeatureState.objects.get(environment=self.environment, feature=self.feature)
        url = reverse('api-v1:environments:environment-featurestates-detail',
                      args=[self.environment.api_key, feature_state.id])
        new_value = 'new-value'
        data = {
            'id': feature_state.id,
            'feature_state_value': new_value,
            'enabled': False,
            'feature': self.feature.id,
            'environment': self.environment.id,
            'identity': None,
            'feature_segment': None
        }

        # When
        self.client.put(url, data=json.dumps(data), content_type='application/json')

        # Then
        feature_state.refresh_from_db()
        assert feature_state.get_feature_state_value() == new_value

    def test_can_filter_feature_states_to_show_identity_overrides_only(self):
        # Given
        feature_state = FeatureState.objects.get(environment=self.environment, feature=self.feature)

        identifier = 'test-identity'
        identity = Identity.objects.create(identifier=identifier, environment=self.environment)
        identity_feature_state = FeatureState.objects.create(environment=self.environment, feature=self.feature,
                                                             identity=identity)

        base_url = reverse('api-v1:environments:environment-featurestates-list', args=[self.environment.api_key])
        url = base_url + '?anyIdentity&feature=' + str(self.feature.id)

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        assert len(res.json().get('results')) == 1

        # and
        assert res.json()['results'][0]['identity']['identifier'] == identifier


@pytest.mark.django_db
class SDKFeatureStatesTestCase(APITestCase):
    def setUp(self) -> None:
        self.environment_fs_value = 'environment'
        self.identity_fs_value = 'identity'
        self.segment_fs_value = 'segment'

        self.organisation = Organisation.objects.create(name='Test organisation')
        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment = Environment.objects.create(name='Test environment', project=self.project)
        self.feature = Feature.objects.create(name='Test feature', project=self.project, type=CONFIG, initial_value=self.environment_fs_value)
        segment = Segment.objects.create(name='Test segment', project=self.project)
        FeatureSegment.objects.create(segment=segment, feature=self.feature, value=self.segment_fs_value)
        identity = Identity.objects.create(identifier='test', environment=self.environment)
        identity_feature_state = FeatureState.objects.create(identity=identity, environment=self.environment, feature=self.feature)
        FeatureStateValue.objects.filter(feature_state=identity_feature_state).update(string_value=self.identity_fs_value)

        self.url = reverse('api-v1:flags')

        self.client.credentials(HTTP_X_ENVIRONMENT_KEY=self.environment.api_key)

    def test_get_flags(self):
        # Given - setup data which includes a single feature overridden by a segment and an identity

        # When - we get flags
        response = self.client.get(self.url)

        # Then - we only get a single flag back and that is the environment default
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert len(response_json) == 1
        assert response_json[0]["feature"]["id"] == self.feature.id
        assert response_json[0]["feature_state_value"] == self.environment_fs_value
