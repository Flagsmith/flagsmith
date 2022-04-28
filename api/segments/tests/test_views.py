import json

from core.constants import STRING
from django.contrib.auth import get_user_model
from django.urls import reverse
from flag_engine.api.document_builders import build_identity_document
from rest_framework import status
from rest_framework.test import APITestCase

from audit.models import AuditLog, RelatedObjectType
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from segments.models import EQUAL, Condition, Segment, SegmentRule

User = get_user_model()


class SegmentViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create(email="test@example.com")
        self.organisation = Organisation.objects.create(name="Test Organisation")
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)
        self.client.force_authenticate(self.user)
        self.project = Project.objects.create(
            name="Test project", organisation=self.organisation
        )

    def tearDown(self) -> None:
        AuditLog.objects.all().delete()

    def test_audit_log_created_when_segment_created(self):
        # Given
        url = reverse("api-v1:projects:project-segments-list", args=[self.project.id])
        data = {
            "name": "Test Segment",
            "project": self.project.id,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        }

        # When
        res = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_201_CREATED
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.SEGMENT.name
            ).count()
            == 1
        )

    def test_audit_log_created_when_segment_updated(self):
        # Given
        segment = Segment.objects.create(name="Test segment", project=self.project)
        url = reverse(
            "api-v1:projects:project-segments-detail",
            args=[self.project.id, segment.id],
        )
        data = {
            "name": "New segment name",
            "project": self.project.id,
            "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        }

        # When
        res = self.client.put(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_200_OK
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.SEGMENT.name
            ).count()
            == 1
        )

    def test_can_filter_by_identity_to_get_only_matching_segments(self):
        # Given
        trait_key = "trait_key"
        trait_value = "trait_value"

        matching_segment = Segment.objects.create(
            name="Matching segment", project=self.project
        )
        matching_rule = SegmentRule.objects.create(
            segment=matching_segment, type=SegmentRule.ALL_RULE
        )
        Condition.objects.create(
            rule=matching_rule, property=trait_key, operator=EQUAL, value=trait_value
        )

        Segment.objects.create(name="Non matching segment", project=self.project)

        environment = Environment.objects.create(
            name="Test environment", project=self.project
        )
        identity = Identity.objects.create(
            identifier="test-user", environment=environment
        )
        Trait.objects.create(
            identity=identity,
            trait_key=trait_key,
            value_type=STRING,
            string_value=trait_value,
        )

        base_url = reverse(
            "api-v1:projects:project-segments-list", args=[self.project.id]
        )
        url = base_url + "?identity=%d" % identity.id

        # When
        res = self.client.get(url)

        # Then
        assert res.json().get("count") == 1

    def test_cannot_create_segments_without_rules(self):
        # Given
        url = reverse("api-v1:projects:project-segments-list", args=[self.project.id])
        data = {"name": "New segment name", "project": self.project.id, "rules": []}

        # When
        res = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_can_create_segments_with_boolean_condition(self):
        # Given
        url = reverse("api-v1:projects:project-segments-list", args=[self.project.id])
        data = {
            "name": "New segment name",
            "project": self.project.id,
            "rules": [
                {
                    "type": "ALL",
                    "rules": [],
                    "conditions": [
                        {"operator": EQUAL, "property": "test-property", "value": True}
                    ],
                }
            ],
        }

        # When
        res = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_201_CREATED


def test_can_filter_by_edge_identity_to_get_only_matching_segments(
    project, environment, identity, admin_client, identity_matching_segment, mocker
):
    # Given
    Segment.objects.create(name="Non matching segment", project=project)
    expected_segment_ids = [identity_matching_segment.id]
    identity_document = build_identity_document(identity)
    identity_uuid = identity_document["identity_uuid"]
    mocked_identity_wrapper = mocker.patch(
        "environments.identities.models.Identity.dynamo_wrapper",
    )

    mocked_identity_wrapper.get_segmenent_ids.return_value = expected_segment_ids

    base_url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    url = f"{base_url}?identity={identity_uuid}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.json().get("count") == len(expected_segment_ids)
    assert response.json()["results"][0]["id"] == expected_segment_ids[0]
    mocked_identity_wrapper.get_segmenent_ids.assert_called_with(identity_uuid)
