import json
import random

import pytest
from common.projects.permissions import (
    MANAGE_SEGMENTS,
    VIEW_PROJECT,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from flag_engine.segments.constants import EQUAL
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.constants import SEGMENT_DELETED_MESSAGE
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from metadata.models import Metadata, MetadataModelField
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule, WhitelistedSegment
from tests.types import WithProjectPermissionsCallable
from util.mappers import map_identity_to_identity_document
from segments.services import SegmentCloner

User = get_user_model()


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_filter_by_identity_to_get_only_matching_segments(  # type: ignore[no-untyped-def]
    project, client, environment, identity, trait, identity_matching_segment, segment
):
    # Given
    base_url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    url = base_url + "?identity=%d" % identity.id

    # When
    res = client.get(url)

    # Then
    assert res.json().get("count") == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_cannot_create_segments_without_rules(project, client):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {"name": "New segment name", "project": project.id, "rules": []}

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_create_segments_with_boolean_condition(project, client):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
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
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_create_segments_with_condition_that_has_null_value(project, client):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [{"operator": EQUAL, "property": "test-property"}],
            }
        ],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segments_reaching_max_limit(project, client, settings):  # type: ignore[no-untyped-def]
    # Given
    # let's reduce the max segments allowed to 1
    project.max_segments_allowed = 1
    project.save()

    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [{"operator": EQUAL, "property": "test-property"}],
            }
        ],
    }

    # Now, let's create the first segment
    res = client.post(url, data=json.dumps(data), content_type="application/json")
    assert res.status_code == status.HTTP_201_CREATED

    # Then
    # Let's try to create a second segment
    res = client.post(url, data=json.dumps(data), content_type="application/json")
    assert res.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        res.json()["project"]
        == "The project has reached the maximum allowed segments limit."
    )
    assert project.segments.count() == 1


def test_segments_limit_ignores_old_segment_versions(
    project: Project,
    segment: Segment,
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS])  # type: ignore[call-arg]

    # let's reduce the max segments allowed to 2
    project.max_segments_allowed = 2
    project.save()

    # and create some older versions for the segment fixture
    SegmentCloner(segment).deep_clone()
    assert Segment.objects.filter(version_of_id=segment.id).count() == 3
    assert Segment.live_objects.count() == 1

    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [{"operator": EQUAL, "property": "test-property"}],
            }
        ],
    }

    # When
    res = staff_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_segment_updated(project, client):  # type: ignore[no-untyped-def]
    # Given
    segment = Segment.objects.create(name="Test segment", project=project)
    url = reverse(
        "api-v1:projects:project-segments-detail",
        args=[project.id, segment.id],
    )
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.SEGMENT.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_patch_segment(project, segment, client):  # type: ignore[no-untyped-def]
    # Given
    segment = Segment.objects.create(name="Test segment", project=project)
    url = reverse(
        "api-v1:projects:project-segments-detail",
        args=[project.id, segment.id],
    )
    data = {
        "name": "New segment name",
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    res = client.patch(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_segment_deleted(project, segment, client):  # type: ignore[no-untyped-def]
    # Given
    segment = Segment.objects.create(name="Test segment", project=project)
    url = reverse(
        "api-v1:projects:project-segments-detail",
        args=[project.id, segment.id],
    )

    # When
    res = client.delete(url, content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_204_NO_CONTENT
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.SEGMENT.name,
            log=SEGMENT_DELETED_MESSAGE % segment.name,
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_segment_created(project, client):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "Test Segment",
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED

    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.SEGMENT.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_filter_by_edge_identity_to_get_only_matching_segments(  # type: ignore[no-untyped-def]
    project,
    environment,
    identity,
    identity_matching_segment,
    edge_identity_dynamo_wrapper_mock,
    client,
):
    # Given
    Segment.objects.create(name="Non matching segment", project=project)
    expected_segment_ids = [identity_matching_segment.id]
    identity_document = map_identity_to_identity_document(identity)
    identity_uuid = identity_document["identity_uuid"]

    edge_identity_dynamo_wrapper_mock.get_segment_ids.return_value = (
        expected_segment_ids
    )

    base_url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    url = f"{base_url}?identity={identity_uuid}"

    # When
    response = client.get(url)

    # Then
    assert response.json().get("count") == len(expected_segment_ids)
    assert response.json()["results"][0]["id"] == expected_segment_ids[0]
    edge_identity_dynamo_wrapper_mock.get_segment_ids.assert_called_with(identity_uuid)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_associated_features_returns_all_the_associated_features(  # type: ignore[no-untyped-def]
    project, environment, feature, segment, segment_featurestate, client
):
    # Given
    # Firstly, let's create extra environment and feature to make sure we
    # have some features that are not associated with the segment
    Environment.objects.create(name="Another environment", project=project)
    Feature.objects.create(name="another feature", project=project)

    url = reverse(
        "api-v1:projects:project-segments-associated-features",
        args=[project.id, segment.id],
    )
    # When
    response = client.get(url)

    # Then
    assert response.json().get("count") == 1
    assert response.json()["results"][0]["id"] == segment_featurestate.id
    assert response.json()["results"][0]["feature"] == feature.id
    assert response.json()["results"][0]["environment"] == environment.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_associated_features_returns_only_latest_versions_of_associated_features(
    project: Project,
    segment: Segment,
    environment_v2_versioning: Environment,
    client: APIClient,
) -> None:
    # Given
    # 2 features
    feature_one = Feature.objects.create(project=project, name="feature_1")
    feature_two = Feature.objects.create(project=project, name="feature_2")

    # Now let's create a version for each feature with a segment override
    for feature in (feature_one, feature_two):
        version = EnvironmentFeatureVersion.objects.create(
            feature=feature, environment=environment_v2_versioning
        )
        FeatureState.objects.create(
            feature=feature,
            environment=environment_v2_versioning,
            environment_feature_version=version,
            feature_segment=FeatureSegment.objects.create(
                segment=segment,
                environment=environment_v2_versioning,
                feature=feature,
                environment_feature_version=version,
            ),
        )
        version.publish()

    # And then let's create a third version for feature_one where we update the segment override
    feature_1_version_3 = EnvironmentFeatureVersion.objects.create(
        feature=feature_one, environment=environment_v2_versioning
    )
    f1v3_segment_override_feature_state = feature_1_version_3.feature_states.get(
        feature_segment__segment=segment
    )
    f1v3_segment_override_feature_state.enabled = True
    f1v3_segment_override_feature_state.save()
    feature_1_version_3.publish()

    # And finally, let's create a third version for feature_two where we remove the segment override
    feature_2_version_3 = EnvironmentFeatureVersion.objects.create(
        feature=feature_two, environment=environment_v2_versioning
    )
    feature_2_version_3.feature_states.filter(feature_segment__segment=segment).delete()
    feature_2_version_3.publish()

    url = "%s?environment=%s" % (
        reverse(
            "api-v1:projects:project-segments-associated-features",
            args=[project.id, segment.id],
        ),
        environment_v2_versioning.id,
    )

    # When
    response = client.get(url)

    # Then
    assert response.json().get("count") == 1
    assert response.json()["results"][0]["id"] == f1v3_segment_override_feature_state.id
    assert response.json()["results"][0]["feature"] == feature_one.id
    assert response.json()["results"][0]["environment"] == environment_v2_versioning.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_can_create_feature_based_segment(project, client, feature):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "Test Segment",
        "project": project.id,
        "feature": feature.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    res = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["feature"] == feature.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_segment_by_uuid(client, project, segment):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:segments:get-segment-by-uuid", args=[segment.uuid])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["id"] == segment.id
    assert response.json()["uuid"] == str(segment.uuid)


@pytest.mark.skipif(
    settings.IS_RBAC_INSTALLED is True,
    reason="Skip this test if RBAC is installed",
)
@pytest.mark.parametrize(
    "client, num_queries",
    [
        (lazy_fixture("admin_master_api_key_client"), 12),
        (lazy_fixture("admin_client"), 14),
    ],
)
def test_list_segments_num_queries_without_rbac(
    django_assert_num_queries: DjangoAssertNumQueries,
    project: Project,
    client: APIClient,
    num_queries: int,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    num_segments = 5
    _list_segment_setup_data(project, required_a_segment_metadata_field, num_segments)

    # When
    with django_assert_num_queries(num_queries):
        # TODO: improve this
        #  I've removed the N+1 issue using prefetch related but there is still an overlap on permission checks
        #  and we can probably use varying serializers for the segments since we only allow certain structures via
        #  the UI (but the serializers allow for infinite nesting)
        response = client.get(
            reverse("api-v1:projects:project-segments-list", args=[project.id])
        )

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == num_segments


@pytest.mark.skipif(
    settings.IS_RBAC_INSTALLED is False,
    reason="Skip this test if RBAC is not installed",
)
@pytest.mark.parametrize(
    "client, num_queries",
    [
        (lazy_fixture("admin_master_api_key_client"), 12),
        (lazy_fixture("admin_client"), 15),
    ],
)
def test_list_segments_num_queries_with_rbac(
    django_assert_num_queries: DjangoAssertNumQueries,
    project: Project,
    client: APIClient,
    num_queries: int,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:  # pragma: no cover
    # Given
    num_segments = 5
    _list_segment_setup_data(project, required_a_segment_metadata_field, num_segments)

    # When
    with django_assert_num_queries(num_queries):
        response = client.get(
            reverse("api-v1:projects:project-segments-list", args=[project.id])
        )

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == num_segments


def _list_segment_setup_data(
    project: Project,
    required_a_segment_metadata_field: MetadataModelField,
    num_segments: int,
) -> None:
    for i in range(num_segments):
        segment = Segment.objects.create(project=project, name=f"segment {i}")
        Metadata.objects.create(
            object_id=segment.id,
            content_type=ContentType.objects.get_for_model(segment),
            model_field=required_a_segment_metadata_field,
            field_value="test",
        )
        all_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        any_rule = SegmentRule.objects.create(rule=all_rule, type=SegmentRule.ANY_RULE)
        Condition.objects.create(
            property="foo", value=str(random.randint(0, 10)), rule=any_rule
        )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_search_segments(django_assert_num_queries, project, client):  # type: ignore[no-untyped-def]
    # Given
    segments = []
    segment_names = ["segment one", "segment two"]

    for segment_name in segment_names:
        segment = Segment.objects.create(project=project, name=segment_name)
        all_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        any_rule = SegmentRule.objects.create(rule=all_rule, type=SegmentRule.ANY_RULE)
        Condition.objects.create(
            property="foo", value=str(random.randint(0, 10)), rule=any_rule
        )
        segments.append(segment)

    url = "%s?q=%s" % (
        reverse("api-v1:projects:project-segments-list", args=[project.id]),
        segment_names[0].split()[1],
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["name"] == segment_names[0]


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segments_with_description_condition(project, client):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    data = {
        "name": "New segment name",
        "project": project.id,
        "rules": [
            {
                "type": "ALL",
                "rules": [],
                "conditions": [
                    {
                        "operator": EQUAL,
                        "property": "test-property",
                        "value": True,
                        "description": "test-description",
                    }
                ],
            }
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    segment_condition_description_value = response.json()["rules"][0]["conditions"][0][
        "description"
    ]
    assert segment_condition_description_value == "test-description"


def test_update_segment_add_new_condition(
    project: Project,
    admin_client_new: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    new_condition_property = "foo2"
    new_condition_value = "bar"
    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            # existing condition
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            # new condition
                            {
                                "property": new_condition_property,
                                "operator": EQUAL,
                                "value": new_condition_value,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert nested_rule.conditions.count() == 2
    assert (
        nested_rule.conditions.order_by("-id").first().property
        == new_condition_property
    )
    assert nested_rule.conditions.order_by("-id").first().value == new_condition_value


def test_update_mismatched_rule_and_segment(
    project: Project,
    admin_client_new: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    false_segment = Segment.objects.create(name="False segment", project=project)
    segment_rule.segment = false_segment
    segment_rule.save()

    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    new_condition_property = "foo2"
    new_condition_value = "bar"
    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            # existing condition
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            # new condition
                            {
                                "property": new_condition_property,
                                "operator": EQUAL,
                                "value": new_condition_value,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"segment": "Mismatched segment is not allowed"}
    segment_rule.refresh_from_db()
    assert segment_rule.segment == false_segment


def test_update_mismatched_condition_and_segment(
    project: Project,
    admin_client_new: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    false_segment = Segment.objects.create(name="False segment", project=project)
    false_segment_rule = SegmentRule.objects.create(
        segment=false_segment, type=SegmentRule.ALL_RULE
    )
    false_nested_rule = SegmentRule.objects.create(
        rule=false_segment_rule, type=SegmentRule.ANY_RULE
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )

    existing_condition = Condition.objects.create(
        rule=false_nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    new_condition_property = "foo2"
    new_condition_value = "bar"
    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            # existing condition
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            # new condition
                            {
                                "property": new_condition_property,
                                "operator": EQUAL,
                                "value": new_condition_value,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"segment": "Mismatched segment is not allowed"}
    existing_condition.refresh_from_db()
    assert existing_condition._get_segment() != segment


def test_update_segment_versioned_segment(
    project: Project,
    admin_client_new: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    # Before updating the segment confirm pre-existing version count which is
    # automatically set by the fixture.
    assert Segment.objects.filter(version_of=segment).count() == 2

    new_condition_property = "foo2"
    new_condition_value = "bar"
    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            # existing condition
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            # new condition
                            {
                                "property": new_condition_property,
                                "operator": EQUAL,
                                "value": new_condition_value,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Now verify that a new versioned segment has been set.
    assert Segment.objects.filter(version_of=segment).count() == 3

    # Now check the previously versioned segment to match former count of conditions.

    versioned_segment = Segment.objects.filter(version_of=segment, version=2).first()
    assert versioned_segment != segment
    assert versioned_segment.rules.count() == 1
    versioned_rule = versioned_segment.rules.first()
    assert versioned_rule.rules.count() == 1

    nested_versioned_rule = versioned_rule.rules.first()
    assert nested_versioned_rule.conditions.count() == 1
    versioned_condition = nested_versioned_rule.conditions.first()
    assert versioned_condition != existing_condition
    assert versioned_condition.property == existing_condition.property


def test_update_segment_versioned_segment_with_thrown_exception(
    project: Project,
    admin_client_new: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    assert segment.version == 2 == Segment.objects.filter(version_of=segment).count()

    new_condition_property = "foo2"
    new_condition_value = "bar"
    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            {
                                "property": new_condition_property,
                                "operator": EQUAL,
                                "value": new_condition_value,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    update_super_patch = mocker.patch(
        "rest_framework.serializers.ModelSerializer.update"
    )
    update_super_patch.side_effect = Exception("Mocked exception")

    # When
    with pytest.raises(Exception):
        admin_client_new.put(
            url, data=json.dumps(data), content_type="application/json"
        )

    # Then
    segment.refresh_from_db()

    # Now verify that the version of the segment has not been changed.
    assert segment.version == 2 == Segment.objects.filter(version_of=segment).count()


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_segment_delete_existing_condition(  # type: ignore[no-untyped-def]
    project, client, segment, segment_rule
):
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                                "delete": True,
                            },
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert nested_rule.conditions.count() == 0


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_segment_delete_existing_rule(project, client, segment, segment_rule):  # type: ignore[no-untyped-def]
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )

    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [],
                    }
                ],
                "conditions": [],
                "delete": True,
            }
        ],
    }

    # When
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert segment_rule.conditions.count() == 0


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_segment_metadata_create_correct_number_of_metadata(
    project: Project,
    client: APIClient,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    first_segment_data = {
        "name": "Test Segment",
        "description": description,
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        "metadata": [
            {
                "model_field": required_a_segment_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }
    second_segment_data = {
        "name": "Test Segment",
        "description": description,
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        "metadata": [
            {
                "model_field": required_a_segment_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response_first = client.post(
        url, data=json.dumps(first_segment_data), content_type="application/json"
    )
    response_second = client.post(
        url, data=json.dumps(second_segment_data), content_type="application/json"
    )
    # Then
    assert response_first.status_code == status.HTTP_201_CREATED
    assert response_second.status_code == status.HTTP_201_CREATED
    assert (
        response_first.json()["metadata"][0]["model_field"]
        == required_a_segment_metadata_field.id
    )
    assert (
        response_second.json()["metadata"][0]["model_field"]
        == required_a_segment_metadata_field.id
    )

    metadata = Metadata.objects.filter(
        model_field=required_a_segment_metadata_field.id
    ).all()
    assert metadata.count() == 2


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_with_required_metadata_returns_201(
    project: Project,
    client: APIClient,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test Segment",
        "description": description,
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        "metadata": [
            {
                "model_field": required_a_segment_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == required_a_segment_metadata_field.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_with_required_metadata_using_organisation_content_type_returns_201(
    project: Project,
    client: APIClient,
    required_a_segment_metadata_field_using_organisation_content_type: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test Segment",
        "description": description,
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        "metadata": [
            {
                "model_field": required_a_segment_metadata_field_using_organisation_content_type.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == required_a_segment_metadata_field_using_organisation_content_type.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_without_required_metadata_returns_400(
    project: Project,
    client: APIClient,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    description = "This is the description"
    data = {
        "name": "Test Segment",
        "description": description,
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_segment_obeys_max_conditions(
    project: Project,
    admin_client: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
    settings: SettingsWrapper,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    # Reduce value for test debugging.
    settings.SEGMENT_RULES_CONDITIONS_LIMIT = 10
    new_condition_property = "prop_"
    new_condition_value = "red"
    new_conditions = []
    for i in range(settings.SEGMENT_RULES_CONDITIONS_LIMIT):
        new_conditions.append(
            {
                "property": f"{new_condition_property}{i}",
                "operator": EQUAL,
                "value": new_condition_value,
            }
        )

    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            *new_conditions,
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "segment": "The segment has 11 conditions, which exceeds the maximum condition count of 10."
    }

    nested_rule.refresh_from_db()
    assert nested_rule.conditions.count() == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_with_optional_metadata_returns_201(
    project: Project,
    client: APIClient,
    optional_b_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test Segment",
        "description": description,
        "project": project.id,
        "rules": [{"type": "ALL", "rules": [], "conditions": []}],
        "metadata": [
            {
                "model_field": optional_b_segment_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == optional_b_segment_metadata_field.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


def test_update_segment_evades_max_conditions_when_whitelisted(
    project: Project,
    admin_client: APIClient,
    segment: Segment,
    segment_rule: SegmentRule,
    settings: SettingsWrapper,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-detail", args=[project.id, segment.id]
    )
    nested_rule = SegmentRule.objects.create(
        rule=segment_rule, type=SegmentRule.ANY_RULE
    )
    existing_condition = Condition.objects.create(
        rule=nested_rule, property="foo", operator=EQUAL, value="bar"
    )

    # Create the whitelist to stop the validation.
    WhitelistedSegment.objects.create(segment=segment)

    # Reduce value for test debugging.
    settings.SEGMENT_RULES_CONDITIONS_LIMIT = 10
    new_condition_property = "prop_"
    new_condition_value = "red"
    new_conditions = []
    for i in range(settings.SEGMENT_RULES_CONDITIONS_LIMIT):
        new_conditions.append(
            {
                "property": f"{new_condition_property}{i}",
                "operator": EQUAL,
                "value": new_condition_value,
            }
        )

    data = {
        "name": segment.name,
        "project": project.id,
        "rules": [
            {
                "id": segment_rule.id,
                "type": segment_rule.type,
                "rules": [
                    {
                        "id": nested_rule.id,
                        "type": nested_rule.type,
                        "rules": [],
                        "conditions": [
                            {
                                "id": existing_condition.id,
                                "property": existing_condition.property,
                                "operator": existing_condition.operator,
                                "value": existing_condition.value,
                            },
                            *new_conditions,
                        ],
                    }
                ],
                "conditions": [],
            }
        ],
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    nested_rule.refresh_from_db()
    assert nested_rule.conditions.count() == 11


def test_create_segment_obeys_max_conditions(
    project: Project,
    admin_client: APIClient,
    settings: SettingsWrapper,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-segments-list", args=[project.id])

    # Reduce value for test debugging.
    settings.SEGMENT_RULES_CONDITIONS_LIMIT = 10
    new_condition_property = "prop_"
    new_condition_value = "red"
    new_conditions = []
    for i in range(settings.SEGMENT_RULES_CONDITIONS_LIMIT + 1):
        new_conditions.append(
            {
                "property": f"{new_condition_property}{i}",
                "operator": EQUAL,
                "value": new_condition_value,
            }
        )

    data = {
        "name": "segment_name",
        "project": project.id,
        "rules": [
            {
                "conditions": [],
                "type": "ALL",
                "rules": [
                    {
                        "type": "ANY",
                        "rules": [],
                        "conditions": [
                            *new_conditions,
                        ],
                    }
                ],
            }
        ],
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "segment": "The segment has 11 conditions, which exceeds the maximum condition count of 10."
    }
    assert Segment.objects.count() == 0


def test_include_feature_specific_query_filter__true(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    segment: Segment,
    feature_specific_segment: Segment,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS, VIEW_PROJECT])  # type: ignore[call-arg]
    url = "%s?include_feature_specific=1" % (
        reverse("api-v1:projects:project-segments-list", args=[project.id]),
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.json()["count"] == 2
    assert [res["id"] for res in response.json()["results"]] == [
        segment.id,
        feature_specific_segment.id,
    ]


def test_include_feature_specific_query_filter__false(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    segment: Segment,
    feature_specific_segment: Segment,
) -> None:
    # Given
    with_project_permissions([MANAGE_SEGMENTS, VIEW_PROJECT])  # type: ignore[call-arg]
    url = "%s?include_feature_specific=0" % (
        reverse("api-v1:projects:project-segments-list", args=[project.id]),
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.json()["count"] == 1
    assert [res["id"] for res in response.json()["results"]] == [segment.id]


@pytest.mark.parametrize(
    "source_segment",
    [
        (lazy_fixture("segment")),
        (lazy_fixture("feature_specific_segment")),
    ],
)
def test_clone_segment(
    project: Project,
    admin_client: APIClient,
    source_segment: Segment,
    required_a_segment_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-clone", args=[project.id, source_segment.id]
    )
    new_segment_name = "cloned_segment"
    data = {
        "name": new_segment_name,
    }
    # Preparing the rules
    segment_rule = SegmentRule.objects.create(
        segment=source_segment,
        type=SegmentRule.ALL_RULE,
    )
    sub_rule = SegmentRule.objects.create(
        rule=segment_rule,
        type=SegmentRule.ALL_RULE,
    )

    # Preparing the conditions
    created_condition = Condition.objects.create(
        rule=sub_rule,
        property="foo",
        operator=EQUAL,
        value="bar",
        created_with_segment=False,
    )

    # Preparing the metadata
    segment_content_type = ContentType.objects.get_for_model(source_segment)
    metadata = Metadata.objects.create(
        object_id=source_segment.id,
        content_type=segment_content_type,
        model_field=required_a_segment_metadata_field,
        field_value="test-clone-segment-metadata",
    )

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_data = response.json()
    assert response_data["name"] == new_segment_name
    assert response_data["project"] == project.id
    assert response_data["id"] != source_segment.id

    # Testing cloned segment main attributes
    cloned_segment = Segment.objects.get(id=response_data["id"])
    assert cloned_segment.name == new_segment_name
    assert cloned_segment.project_id == project.id
    assert cloned_segment.description == source_segment.description
    assert cloned_segment.version == 1
    assert cloned_segment.version_of_id == cloned_segment.id
    assert cloned_segment.change_request is None
    assert cloned_segment.feature_id == source_segment.feature_id

    # Testing cloning of rules
    assert cloned_segment.rules.count() == source_segment.rules.count()

    cloned_top_rule = cloned_segment.rules.first()
    cloned_sub_rule = cloned_top_rule.rules.first()

    assert cloned_top_rule.type == segment_rule.type
    assert cloned_sub_rule.type == segment_rule.type

    # Testing cloning of sub-rules conditions
    cloned_condition = cloned_sub_rule.conditions.first()

    assert cloned_condition.property == created_condition.property
    assert cloned_condition.operator == created_condition.operator
    assert cloned_condition.value == created_condition.value

    # Testing cloning of metadata
    cloned_metadata = cloned_segment.metadata.first()
    assert cloned_metadata.model_field == metadata.model_field
    assert cloned_metadata.field_value == metadata.field_value
    assert cloned_metadata.id != metadata.id


def test_clone_segment_without_name_should_fail(
    project: Project,
    admin_client: APIClient,
    segment: Segment,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-segments-clone", args=[project.id, segment.id]
    )
    data = {
        "no-name": "",
    }
    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
