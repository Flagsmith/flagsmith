import json
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog, RelatedObjectType, IDENTITY_FEATURE_STATE_UPDATED_MESSAGE, \
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE
from environments.models import Environment, Identity
from features.models import Feature, FeatureState, FeatureSegment
from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment
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

        user.organisations.add(self.organisation)

        self.project = Project.objects.create(name='Test project', organisation=self.organisation)
        self.environment_1 = Environment.objects.create(name='Test environment 1', project=self.project)
        self.environment_2 = Environment.objects.create(name='Test environment 2', project=self.project)

    def tearDown(self) -> None:
        AuditLog.objects.all().delete()
        Feature.objects.all().delete()
        FeatureState.objects.all().delete()
        Segment.objects.all().delete()
        FeatureSegment.objects.all().delete()
        Identity.objects.all().delete()

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
        url = reverse('api:v1:projects:project-features-list', args=[self.project.id])
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
        url = reverse('api:v1:projects:project-features-detail', args=[self.project.id, feature.id])
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
        url = reverse('api:v1:projects:project-features-segments', args=[self.project.id, feature.id])
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
        url = reverse('api:v1:environments:identity-featurestates-list', args=[self.environment_1.api_key,
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
        url = reverse('api:v1:environments:identity-featurestates-detail', args=[self.environment_1.api_key,
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
        url = reverse('api:v1:environments:identity-featurestates-detail', args=[self.environment_1.api_key,
                                                                                 identity.id, feature_state.id])

        # When
        res = self.client.delete(url)

        # Then
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE_STATE.name).count() == 1

        # and
        expected_log_message = IDENTITY_FEATURE_STATE_DELETED_MESSAGE % (feature.name, identity.identifier)
        audit_log = AuditLog.objects.get(related_object_type=RelatedObjectType.FEATURE_STATE.name)
        assert audit_log.log == expected_log_message

    def test_feature_state_values_should_be_updated_when_feature_initial_value_updated(self):
        # Given
        feature = Feature.objects.create(name='test-feature', project=self.project, type='CONFIG',
                                         initial_value='initial-value')
        new_value = 'new-value'
        url = reverse('api:v1:projects:project-features-detail', args=[self.project.id, feature.id])
        data = {
            'initial_value': new_value
        }

        # When
        response = self.client.patch(url, data=data)

        # Then
        assert response.status_code == status.HTTP_200_OK

        # check feature state value was updated in all environments
        assert all(feature_state.get_feature_state_value() == new_value
                   for feature_state in FeatureState.objects.filter(feature=feature))


@pytest.mark.django_db
class FeatureSegmentViewTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name='Test Org')

        user.organisations.add(organisation)

        self.project = Project.objects.create(organisation=organisation, name='Test project')
        self.environment_1 = Environment.objects.create(project=self.project, name='Test environment 1')
        self.environment_2 = Environment.objects.create(project=self.project, name='Test environment 2')
        self.feature = Feature.objects.create(project=self.project, name='Test feature')
        self.segment = Segment.objects.create(project=self.project, name='Test segment')

    def test_when_feature_segments_updated_then_feature_states_updated_for_each_environment(self):
        # Given
        url = reverse('api:v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
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
        url = reverse('api:v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
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
        url = reverse('api:v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
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
        url = reverse('api:v1:projects:project-features-segments', args=[self.project.id, self.feature.id])
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
