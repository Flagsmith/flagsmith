import json
from unittest.case import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from audit.models import (
    SEGMENT_FEATURE_STATE_DELETED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import Segment
from util.tests import Helper


@pytest.mark.django_db
class FeatureSegmentViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=user)

        organisation = Organisation.objects.create(name="Test Org")

        user.add_organisation(organisation, OrganisationRole.ADMIN)

        self.project = Project.objects.create(
            organisation=organisation, name="Test project"
        )
        self.environment_1 = Environment.objects.create(
            project=self.project, name="Test environment 1"
        )
        self.environment_2 = Environment.objects.create(
            project=self.project, name="Test environment 2"
        )
        self.feature = Feature.objects.create(project=self.project, name="Test feature")
        self.segment = Segment.objects.create(project=self.project, name="Test segment")

    def test_list_feature_segments(self):
        # Given
        base_url = reverse("api-v1:features:feature-segment-list")
        url = (
            f"{base_url}?environment={self.environment_1.id}&feature={self.feature.id}"
        )
        segment_2 = Segment.objects.create(project=self.project, name="Segment 2")
        segment_3 = Segment.objects.create(project=self.project, name="Segment 3")

        FeatureSegment.objects.create(
            feature=self.feature, segment=self.segment, environment=self.environment_1
        )
        FeatureSegment.objects.create(
            feature=self.feature, segment=segment_2, environment=self.environment_1
        )
        FeatureSegment.objects.create(
            feature=self.feature, segment=segment_3, environment=self.environment_1
        )
        FeatureSegment.objects.create(
            feature=self.feature, segment=self.segment, environment=self.environment_2
        )

        # When
        response = self.client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK
        response_json = response.json()
        assert response_json["count"] == 3
        for result in response_json["results"]:
            assert result["environment"] == self.environment_1.id

    def test_create_feature_segment(self):
        # Given
        data = {
            "feature": self.feature.id,
            "segment": self.segment.id,
            "environment": self.environment_1.id,
        }
        url = reverse("api-v1:features:feature-segment-list")

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        response_json = response.json()
        assert response_json["id"]

    def test_delete_feature_segment(self):
        # Given
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature, environment=self.environment_1, segment=self.segment
        )
        url = reverse(
            "api-v1:features:feature-segment-detail", args=[feature_segment.id]
        )

        # When
        response = self.client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not FeatureSegment.objects.filter(id=feature_segment.id).exists()

    def test_audit_log_created_when_feature_segment_created(self):
        # Given
        url = reverse("api-v1:features:feature-segment-list")
        data = {
            "segment": self.segment.id,
            "feature": self.feature.id,
            "environment": self.environment_1.id,
        }

        # When
        response = self.client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.FEATURE.name
            ).count()
            == 1
        )

    def test_priority_of_multiple_feature_segments(self):
        # Given
        url = reverse("api-v1:features:feature-segment-update-priorities")

        # another segment and 2 feature segments for the same feature / the 2 segments
        another_segment = Segment.objects.create(
            name="Another segment", project=self.project
        )
        feature_segment_default_data = {
            "environment": self.environment_1,
            "feature": self.feature,
        }
        feature_segment_1 = FeatureSegment.objects.create(
            segment=self.segment, **feature_segment_default_data
        )
        feature_segment_2 = FeatureSegment.objects.create(
            segment=another_segment, **feature_segment_default_data
        )

        # reorder the feature segments
        assert feature_segment_1.priority == 0
        assert feature_segment_2.priority == 1
        data = [
            {"id": feature_segment_1.id, "priority": 1},
            {"id": feature_segment_2.id, "priority": 0},
        ]

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then the segments are reordered
        assert response.status_code == status.HTTP_200_OK
        json_response = response.json()
        assert json_response[0]["id"] == feature_segment_1.id
        assert json_response[1]["id"] == feature_segment_2.id

    def test_delete_feature_segment_creates_audit_log(self):
        # Given
        feature_segment = FeatureSegment.objects.create(
            feature=self.feature, environment=self.environment_1, segment=self.segment
        )
        feature_state = FeatureState.objects.create(
            feature=self.feature,
            environment=self.environment_1,
            feature_segment=feature_segment,
        )

        expected_audit_log_message = SEGMENT_FEATURE_STATE_DELETED_MESSAGE % (
            self.feature.name,
            self.segment.name,
        )

        url = reverse(
            "api-v1:features:feature-segment-detail", args=(feature_segment.id,)
        )

        # When
        response = self.client.delete(url)

        # Then
        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert AuditLog.objects.filter(
            project=self.project,
            related_object_id=feature_state.id,
            related_object_type=RelatedObjectType.FEATURE_STATE.name,
            environment=self.environment_1,
            log=expected_audit_log_message,
        ).exists()
