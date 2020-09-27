import json
from unittest import TestCase, mock

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import AuditLog, RelatedObjectType, IDENTITY_FEATURE_STATE_UPDATED_MESSAGE, \
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE
from environments.models import Environment
from environments.identities.models import Identity
from features.models import Feature, FeatureSegment
from features.feature_states.models import FeatureState
from features.constants import INTEGER, BOOLEAN, STRING, CONFIG
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import Segment
from util.tests import Helper
from projects.tags.models import Tag

# patch this function as it's triggering extra threads and causing errors
mock.patch("features.feature_states.models.trigger_feature_state_change_webhooks").start()


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
        self.project2 = Project.objects.create(name='Test project2', organisation=self.organisation)
        self.environment_1 = Environment.objects.create(name='Test environment 1', project=self.project)
        self.environment_2 = Environment.objects.create(name='Test environment 2', project=self.project)

        self.tag_one = Tag.objects.create(label='Test Tag',
                                         color='#fffff',
                                         description='Test Tag description',
                                         project=self.project)
        self.tag_two = Tag.objects.create(label='Test Tag2',
                                         color='#fffff',
                                         description='Test Tag2 description',
                                         project=self.project)
        self.tag_other_project = Tag.objects.create(label='Wrong Tag',
                                                  color='#fffff',
                                                  description='Test Tag description',
                                                  project=self.project2)

    def test_should_create_feature_states_when_feature_created(self):
        # Given - set up data
        default_value = 'This is a value'
        data = {
            "name": "test feature",
            "initial_value": default_value,
            "type": CONFIG,
            "project": self.project.id,
        }
        url = reverse('api-v1:projects:project-features-list', args=[self.project.id])

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

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
        url = reverse('api-v1:projects:project-features-list', args=[self.project.id])
        data = {
            "name": "test feature",
            "type": CONFIG,
            "initial_value": default_value,
            "project": self.project.id,
        }

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

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
            'initial_value': default_value,
            'type': CONFIG,
            'project': self.project.id,
        }
        url = reverse('api-v1:projects:project-features-list', args=[self.project.id])

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

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
        # check feature was deleted successfully
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

    def test_should_create_tags_when_feature_created(self):
        # Given - set up data
        default_value = "Test"
        feature_name = 'Test feature'
        data = {
            'name': feature_name,
            'project': self.project.id,
            'initial_value': default_value,
            'tags': [self.tag_one.id, self.tag_two.id]
        }

        # When
        response = self.client.post(self.project_features_url % self.project.id,
                                    data=json.dumps(data),
                                    content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED

        # check feature was created successfully
        feature = Feature.objects.filter(name=feature_name, project=self.project.id).first()

        # check tags where added
        assert feature.tags.count() == 2
        self.assertEqual(list(feature.tags.all()), [self.tag_one, self.tag_two])

    def test_when_add_tags_from_different_project_on_feature_create_then_failed(self):
        # Given - set up data
        feature_name = "test feature"
        data = {
            'name': feature_name,
            'project': self.project.id,
            'initial_value': 'test',
            'tags': [self.tag_other_project.id]
        }

        # When
        response = self.client.post(self.project_features_url % self.project.id,
                                   data=json.dumps(data),
                                   content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # check no feature was created successfully
        assert Feature.objects.filter(name=feature_name, project=self.project.id).count() == 0

    def test_when_add_tags_on_feature_update_then_success(self):
        # Given - set up data
        feature = Feature.objects.create(project=self.project, name="test feature")
        data = {
            'name': feature.name,
            'project': self.project.id,
            'tags': [self.tag_one.id]
        }

        # When
        response = self.client.put(self.project_feature_detail_url % (self.project.id, feature.id),
                                   data=json.dumps(data),
                                   content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_200_OK

        # check feature was created successfully
        check_feature = Feature.objects.filter(name=feature.name, project=self.project.id).first()

        # check tags added
        assert check_feature.tags.count() == 1

    def test_when_add_tags_from_different_project_on_feature_update_then_failed(self):
        # Given - set up data
        feature = Feature.objects.create(project=self.project, name="test feature")
        data = {
            'name': feature.name,
            'project': self.project.id,
            'tags': [self.tag_other_project.id]
        }

        # When
        response = self.client.put(self.project_feature_detail_url % (self.project.id, feature.id),
                                   data=json.dumps(data),
                                   content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # check feature was created successfully
        check_feature = Feature.objects.filter(name=feature.name, project=self.project.id).first()

        # check tags not added
        assert check_feature.tags.count() == 0

    def test_list_features(self):
        # Given
        Feature.objects.create(name="test_feature", project=self.project)
        url = reverse("api-v1:projects:project-features-list", args=[self.project.id])

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK

        response_json = response.json()
        assert response_json["count"] == 1

        feature = response_json["results"][0]
        assert "tags" in feature


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

    def test_list_feature_segments(self):
        # Given
        base_url = reverse('api-v1:features:feature-segment-list')
        url = f"{base_url}?environment={self.environment_1.id}&feature={self.feature.id}"
        segment_2 = Segment.objects.create(project=self.project, name='Segment 2')
        segment_3 = Segment.objects.create(project=self.project, name='Segment 3')

        FeatureSegment.objects.create(
            feature=self.feature, segment=self.segment, environment=self.environment_1, value="123", value_type=INTEGER
        )
        FeatureSegment.objects.create(
            feature=self.feature, segment=segment_2, environment=self.environment_1, value="True", value_type=BOOLEAN
        )
        FeatureSegment.objects.create(
            feature=self.feature, segment=segment_3, environment=self.environment_1, value="str", value_type=STRING
        )
        FeatureSegment.objects.create(feature=self.feature, segment=self.segment, environment=self.environment_2)

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["count"] == 3
        for result in response_json["results"]:
            assert result["environment"] == self.environment_1.id

    def test_create_feature_segment_with_integer_value(self):
        # Given
        data = {
            "feature": self.feature.id,
            "segment": self.segment.id,
            "environment": self.environment_1.id,
            "value": 123
        }
        url = reverse("api-v1:features:feature-segment-list")

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["id"]
        assert response_json["value"] == 123

    def test_create_feature_segment_with_boolean_value(self):
        # Given
        data = {
            "feature": self.feature.id,
            "segment": self.segment.id,
            "environment": self.environment_1.id,
            "value": True
        }
        url = reverse("api-v1:features:feature-segment-list")

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["id"]
        assert response_json["value"] is True

    def test_create_feature_segment_with_string_value(self):
        # Given
        data = {
            "feature": self.feature.id,
            "segment": self.segment.id,
            "environment": self.environment_1.id,
            "value": "string"
        }
        url = reverse("api-v1:features:feature-segment-list")

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["id"]
        assert response_json["value"] == "string"

    def test_create_feature_segment_without_value(self):
        # Given
        data = {
            "feature": self.feature.id,
            "segment": self.segment.id,
            "environment": self.environment_1.id,
            "enabled": True
        }
        url = reverse("api-v1:features:feature-segment-list")

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["id"]
        assert response_json["enabled"] is True

    def test_update_feature_segment(self):
        # Given
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature,
            environment=self.environment_1,
            segment=self.segment,
            value="123",
            value_type=INTEGER
        )
        url = reverse("api-v1:features:feature-segment-detail", args=[feature_segment.id])
        data = {
            "value": 456
        }

        # When
        response = self.client.patch(url, data=json.dumps(data), content_type='application/json')

        # Then
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["value"] == 456

    def test_delete_feature_segment(self):
        # Given
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature, environment=self.environment_1, segment=self.segment
        )
        url = reverse("api-v1:features:feature-segment-detail", args=[feature_segment.id])

        # When
        response = self.client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FeatureSegment.objects.filter(id=feature_segment.id).exists()

    def test_audit_log_created_when_feature_segment_created(self):
        # Given
        url = reverse('api-v1:features:feature-segment-list')
        data = {
            'segment': self.segment.id,
            'feature': self.feature.id,
            'environment': self.environment_1.id,
            'enabled': True
        }

        # When
        response = self.client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert AuditLog.objects.filter(related_object_type=RelatedObjectType.FEATURE.name).count() == 1

    def test_priority_of_multiple_feature_segments(self):
        # Given
        url = reverse('api-v1:features:feature-segment-update-priorities')

        # another segment and 2 feature segments for the same feature / the 2 segments
        another_segment = Segment.objects.create(name='Another segment', project=self.project)
        feature_segment_default_data = {"environment": self.environment_1, "feature": self.feature}
        feature_segment_1 = FeatureSegment.objects.create(segment=self.segment, **feature_segment_default_data)
        feature_segment_2 = FeatureSegment.objects.create(segment=another_segment, **feature_segment_default_data)

        # reorder the feature segments
        assert feature_segment_1.priority == 0
        assert feature_segment_2.priority == 1
        data = [
            {
                'id': feature_segment_1.id,
                'priority': 1,
            },
            {
                'id': feature_segment_2.id,
                'priority': 0,
            },
        ]

        # When
        response = self.client.post(url, data=json.dumps(data), content_type='application/json')

        # Then the segments are reordered
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response[0]['id'] == feature_segment_1.id
        assert json_response[1]['id'] == feature_segment_2.id
