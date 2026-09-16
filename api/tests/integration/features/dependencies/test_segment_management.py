import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from features.dependencies.models import SegmentFlagReference
from features.models import Feature, FeatureSegment
from projects.models import Project
from segments.models import Segment


@pytest.fixture(
    params=[False, True],
    ids=["change_requests_disabled", "change_requests_enabled"],
)
def with_and_without_segment_change_requests(
    request: pytest.FixtureRequest,
    project: int,
) -> bool:
    enabled: bool = request.param
    if enabled:
        Project.objects.filter(id=project).update(minimum_change_request_approvals=0)
    return enabled


@pytest.mark.usefixtures("with_and_without_segment_change_requests")
def test_create_segment__valid_flag_dependency__indexes_created(
    admin_client: APIClient,
    project: int,
) -> None:
    # Given
    flag_a = Feature.objects.create(name="flag_a", project_id=project)
    flag_b = Feature.objects.create(name="flag_b", project_id=project)
    flag_c = Feature.objects.create(name="flag_c", project_id=project)

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        data={
            "name": "power_users",
            "rules": [
                {
                    "type": "ALL",
                    "conditions": [
                        {
                            "property": "$.flags.flag_a.enabled",
                            "operator": "EQUAL",
                            "value": True,
                        },
                    ],
                    "rules": [
                        {
                            "type": "ANY",
                            "conditions": [
                                {
                                    "property": "$.flags.flag_b.enabled",
                                    "operator": "EQUAL",
                                    "value": True,
                                },
                                {
                                    "property": "$.flags['flag_c'].enabled",
                                    "operator": "EQUAL",
                                    "value": True,
                                },
                            ],
                        },
                    ],
                }
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 201
    segment_id = response.json()["id"]
    assert list(
        SegmentFlagReference.objects.values(
            "segment",
            "prerequisite_feature",
            "condition_json_path",
        )
    ) == [
        {
            "segment": segment_id,
            "prerequisite_feature": flag_a.id,
            "condition_json_path": "$[0].conditions[0]",
        },
        {
            "segment": segment_id,
            "prerequisite_feature": flag_b.id,
            "condition_json_path": "$[0].rules[0].conditions[0]",
        },
        {
            "segment": segment_id,
            "prerequisite_feature": flag_c.id,
            "condition_json_path": "$[0].rules[0].conditions[1]",
        },
    ]


@pytest.mark.usefixtures("with_and_without_segment_change_requests")
def test_create_segment__nonexistent_prerequisite__responds_400(
    admin_client: APIClient,
    project: int,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        data={
            "name": "segment",
            "rules": [
                {
                    "type": "ALL",
                    "conditions": [
                        {
                            "property": "$.flags.unicorn.enabled",
                            "operator": "EQUAL",
                            "value": True,
                        },
                    ],
                }
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "prerequisite_feature_not_found",
        "prerequisite_feature": "unicorn",
        "condition_json_path": "$[0].conditions[0]",
    }
    assert not Segment.objects.exists()
    assert not SegmentFlagReference.objects.exists()


def test_update_segment_update_rules__valid_flag_dependency__indexes_updated(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    rooster = Feature.objects.create(name="rooster", project_id=project)
    hen = Feature.objects.create(name="hen", project_id=project)
    segment = Segment.objects.create(name="segment", project_id=project)
    SegmentFlagReference.objects.create(
        segment=segment,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[0]",
    )
    SegmentFlagReference.objects.create(
        segment=segment,
        prerequisite_feature=hen,
        condition_json_path="$[0].conditions[1]",
    )
    FeatureSegment.objects.create(
        segment=segment,
        feature=chicken,
        environment_id=environment,
    )

    # When
    response = admin_client.put(
        f"/api/v1/projects/{project}/segments/{segment.id}/",
        data={
            "name": "segment",
            "project": project,
            "rules": [
                {
                    "type": "ALL",
                    "conditions": [
                        {
                            "property": "$.flags.rooster.enabled",
                            "operator": "EQUAL",
                            "value": True,
                        },
                        {
                            "property": "$.flags.hen.enabled",
                            "operator": "EQUAL",
                            "value": True,
                        },
                    ],
                }
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 200
    assert list(
        SegmentFlagReference.objects.values(
            "segment",
            "prerequisite_feature",
            "condition_json_path",
        )
    ) == [
        {
            "segment": segment.id,
            "prerequisite_feature": rooster.id,
            "condition_json_path": "$[0].conditions[0]",
        },
        {
            "segment": segment.id,
            "prerequisite_feature": hen.id,
            "condition_json_path": "$[0].conditions[1]",
        },
    ]
    assert not log.has("dependencies.deleted", prerequisite_feature__name="hen")
    assert not log.has("dependencies.created", prerequisite_feature__name="hen")
    assert log.has(
        "dependencies.deleted",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="chicken",
        prerequisite_feature__name="egg",
    )
    assert log.has(
        "dependencies.created",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="chicken",
        prerequisite_feature__name="rooster",
    )


def test_delete_segment__flag_dependency__indexes_removed(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    segment = Segment.objects.create(name="segment", project_id=project)
    SegmentFlagReference.objects.create(
        segment=segment,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[0]",
    )
    FeatureSegment.objects.create(
        segment=segment,
        feature=chicken,
        environment_id=environment,
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/segments/{segment.id}/",
    )

    # Then
    assert response.status_code == 204
    assert not SegmentFlagReference.objects.exists()
    assert log.has(
        "dependencies.deleted",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="chicken",
        prerequisite_feature__name="egg",
    )


@pytest.mark.usefixtures("with_and_without_segment_change_requests")
def test_update_segment_add_override__circular_flag_dependency__responds_400(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    segment1 = Segment.objects.create(name="segment1", project_id=project)
    segment2 = Segment.objects.create(name="segment2", project_id=project)
    SegmentFlagReference.objects.create(
        segment=segment1,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[1]",
    )
    FeatureSegment.objects.create(
        segment=segment1,
        feature=chicken,
        environment_id=environment,
    )
    SegmentFlagReference.objects.create(
        segment=segment2,
        prerequisite_feature=chicken,
        condition_json_path="$[1].conditions[2]",
    )

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{egg.id}/create-segment-override/",
        data={
            "feature_state_value": {},
            "feature_segment": {"segment": segment2.id},
            "enabled": True,
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "circular_dependency",
        "path": [
            {
                "feature": "egg",
                "needs": "chicken",
                "segment": {
                    "id": segment2.id,
                    "name": segment2.name,
                    "condition_json_path": "$[1].conditions[2]",
                },
            },
            {
                "feature": "chicken",
                "needs": "egg",
                "segment": {
                    "id": segment1.id,
                    "name": segment1.name,
                    "condition_json_path": "$[0].conditions[1]",
                },
            },
        ],
    }
    assert not FeatureSegment.objects.filter(segment=segment2, feature=egg).exists()
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="egg",
        prerequisite_feature__name="chicken",
    )


@pytest.mark.usefixtures("with_and_without_segment_change_requests")
def test_update_segment_add_override__longer_dependency_cycle_path__responds_400(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    rooster = Feature.objects.create(name="rooster", project_id=project)
    segment1 = Segment.objects.create(name="segment1", project_id=project)
    segment2 = Segment.objects.create(name="segment2", project_id=project)
    segment3 = Segment.objects.create(name="segment3", project_id=project)
    SegmentFlagReference.objects.create(
        segment=segment1,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[0]",
    )
    FeatureSegment.objects.create(
        segment=segment1,
        feature=chicken,
        environment_id=environment,
    )
    SegmentFlagReference.objects.create(
        segment=segment2,
        prerequisite_feature=rooster,
        condition_json_path="$[0].conditions[0]",
    )
    FeatureSegment.objects.create(
        segment=segment2,
        feature=egg,
        environment_id=environment,
    )
    SegmentFlagReference.objects.create(
        segment=segment3,
        prerequisite_feature=chicken,
        condition_json_path="$[0].conditions[0]",
    )

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{rooster.id}/create-segment-override/",
        data={
            "feature_state_value": {},
            "feature_segment": {"segment": segment3.id},
            "enabled": True,
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "circular_dependency",
        "path": [
            {
                "feature": "rooster",
                "needs": "chicken",
                "segment": {
                    "id": segment3.id,
                    "name": segment3.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
            {
                "feature": "chicken",
                "needs": "egg",
                "segment": {
                    "id": segment1.id,
                    "name": segment1.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
            {
                "feature": "egg",
                "needs": "rooster",
                "segment": {
                    "id": segment2.id,
                    "name": segment2.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
        ],
    }
    assert not FeatureSegment.objects.filter(segment=segment3, feature=rooster).exists()
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="rooster",
        prerequisite_feature__name="chicken",
    )


def test_update_segment_update_rules__circular_flag_dependency__responds_400(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    segment1 = Segment.objects.create(name="segment1", project_id=project)
    segment2 = Segment.objects.create(name="segment2", project_id=project)
    SegmentFlagReference.objects.create(
        segment=segment1,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[1]",
    )
    FeatureSegment.objects.create(
        segment=segment1,
        feature=chicken,
        environment_id=environment,
    )
    FeatureSegment.objects.create(
        segment=segment2,
        feature=egg,
        environment_id=environment,
    )

    # When
    response = admin_client.put(
        f"/api/v1/projects/{project}/segments/{segment2.id}/",
        data={
            "name": "segment2",
            "project": project,
            "rules": [
                {
                    "type": "ALL",
                    "conditions": [
                        {
                            "property": "$.flags.chicken.enabled",
                            "operator": "EQUAL",
                            "value": True,
                        },
                    ],
                }
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "circular_dependency",
        "path": [
            {
                "feature": "egg",
                "needs": "chicken",
                "segment": {
                    "id": segment2.id,
                    "name": segment2.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
            {
                "feature": "chicken",
                "needs": "egg",
                "segment": {
                    "id": segment1.id,
                    "name": segment1.name,
                    "condition_json_path": "$[0].conditions[1]",
                },
            },
        ],
    }
    assert not SegmentFlagReference.objects.filter(segment=segment2).exists()
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="egg",
        prerequisite_feature__name="chicken",
    )


def test_update_segment_update_rules__longer_dependency_cycle_path__responds_400(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    rooster = Feature.objects.create(name="rooster", project_id=project)
    segment1 = Segment.objects.create(name="segment1", project_id=project)
    segment2 = Segment.objects.create(name="segment2", project_id=project)
    segment3 = Segment.objects.create(name="segment3", project_id=project)
    SegmentFlagReference.objects.create(
        segment=segment1,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[0]",
    )
    FeatureSegment.objects.create(
        segment=segment1,
        feature=chicken,
        environment_id=environment,
    )
    SegmentFlagReference.objects.create(
        segment=segment2,
        prerequisite_feature=rooster,
        condition_json_path="$[0].conditions[0]",
    )
    FeatureSegment.objects.create(
        segment=segment2,
        feature=egg,
        environment_id=environment,
    )
    FeatureSegment.objects.create(
        segment=segment3,
        feature=rooster,
        environment_id=environment,
    )

    # When
    response = admin_client.put(
        f"/api/v1/projects/{project}/segments/{segment3.id}/",
        data={
            "name": "segment3",
            "project": project,
            "rules": [
                {
                    "type": "ALL",
                    "conditions": [
                        {
                            "property": "$.flags.chicken.enabled",
                            "operator": "EQUAL",
                            "value": True,
                        },
                    ],
                }
            ],
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "circular_dependency",
        "path": [
            {
                "feature": "rooster",
                "needs": "chicken",
                "segment": {
                    "id": segment3.id,
                    "name": segment3.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
            {
                "feature": "chicken",
                "needs": "egg",
                "segment": {
                    "id": segment1.id,
                    "name": segment1.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
            {
                "feature": "egg",
                "needs": "rooster",
                "segment": {
                    "id": segment2.id,
                    "name": segment2.name,
                    "condition_json_path": "$[0].conditions[0]",
                },
            },
        ],
    }
    assert not SegmentFlagReference.objects.filter(segment=segment3).exists()
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="rooster",
        prerequisite_feature__name="chicken",
    )


def test_create_feature_segment__circular_flag_dependency__responds_400(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project_id=project)
    egg = Feature.objects.create(name="egg", project_id=project)
    chicken_segment = Segment.objects.create(name="chicken_segment", project_id=project)
    egg_segment = Segment.objects.create(name="egg_segment", project_id=project)
    SegmentFlagReference.objects.create(
        segment=chicken_segment,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[1]",
    )
    FeatureSegment.objects.create(
        segment=chicken_segment,
        feature=chicken,
        environment_id=environment,
    )
    SegmentFlagReference.objects.create(
        segment=egg_segment,
        prerequisite_feature=chicken,
        condition_json_path="$[1].conditions[2]",
    )

    # When
    response = admin_client.post(
        "/api/v1/features/feature-segments/",
        data={
            "feature": egg.id,
            "segment": egg_segment.id,
            "environment": environment,
        },
        format="json",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "circular_dependency",
        "path": [
            {
                "feature": "egg",
                "needs": "chicken",
                "segment": {
                    "id": egg_segment.id,
                    "name": egg_segment.name,
                    "condition_json_path": "$[1].conditions[2]",
                },
            },
            {
                "feature": "chicken",
                "needs": "egg",
                "segment": {
                    "id": chicken_segment.id,
                    "name": chicken_segment.name,
                    "condition_json_path": "$[0].conditions[1]",
                },
            },
        ],
    }
    assert not FeatureSegment.objects.filter(segment=egg_segment, feature=egg).exists()
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="egg",
        prerequisite_feature__name="chicken",
    )
