import json
from typing import Any

import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.versioning.models import EnvironmentFeatureVersion
from metadata.models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from organisations.models import Organisation
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from util.drf_writable_nested.serializers import _is_pk_of


@pytest.fixture()
def other_project() -> Project:
    other_organisation = Organisation.objects.create(name="Other organisation")
    return Project.objects.create(  # type: ignore[no-any-return]
        name="Other project", organisation=other_organisation
    )


@pytest.fixture()
def other_mv_value(other_project: Project) -> MultivariateFeatureStateValue:
    environment = Environment.objects.create(name="Other", project=other_project)
    feature = Feature.objects.create(
        name="other", project=other_project, type="MULTIVARIATE", initial_value="c"
    )
    MultivariateFeatureOption.objects.create(
        feature=feature, type="unicode", string_value="a"
    )
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)
    return feature_state.multivariate_feature_state_values.get()  # type: ignore[no-any-return]


def test_update_segment__other_project_rule_and_condition_ids__leaves_them_untouched(
    admin_client: APIClient,
    project: Project,
    segment: Segment,
    other_project: Project,
) -> None:
    # Given
    other_segment = Segment.objects.create(name="other", project=other_project)
    other_rule = SegmentRule.objects.create(
        segment=other_segment, type=SegmentRule.ALL_RULE
    )
    other_condition = Condition.objects.create(
        rule=other_rule, property="p", operator="EQUAL", value="v"
    )

    # When
    response = admin_client.put(
        f"/api/v1/projects/{project.id}/segments/{segment.id}/",
        data=json.dumps(
            {
                "name": segment.name,
                "project": project.id,
                "rules": [
                    {
                        "id": other_rule.id,
                        "type": "ALL",
                        "rules": [],
                        "conditions": [
                            {
                                "id": other_condition.id,
                                "property": "q",
                                "operator": "EQUAL",
                                "value": "w",
                            }
                        ],
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    other_rule.refresh_from_db()
    other_condition.refresh_from_db()
    assert other_rule.segment == other_segment
    assert (other_condition.rule, other_condition.property) == (other_rule, "p")
    assert segment.rules.get().conditions.get().property == "q"


def test_update_feature__other_project_multivariate_option_id__leaves_it_untouched(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    other_mv_value: MultivariateFeatureStateValue,
) -> None:
    # Given
    other_option = other_mv_value.multivariate_feature_option

    # When
    response = admin_client.put(
        f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/",
        data=json.dumps(
            {
                "name": multivariate_feature.name,
                "type": "MULTIVARIATE",
                "multivariate_options": [
                    {
                        "id": other_option.id,
                        "type": "unicode",
                        "string_value": "mine",
                        "default_percentage_allocation": 10,
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    other_option.refresh_from_db()
    assert (other_option.feature_id, other_option.string_value) == (
        other_mv_value.feature_state.feature_id,
        "a",
    )
    assert multivariate_feature.multivariate_options.get().string_value == "mine"


@pytest.mark.parametrize(
    "url, feature_state_value",
    [
        (
            "/api/v1/environments/{api_key}/featurestates/{id}/",
            "control",
        ),
        (
            "/api/v1/features/featurestates/{id}/",
            {"type": "unicode", "string_value": "control"},
        ),
    ],
)
def test_update_feature_state__other_project_multivariate_value_id__leaves_it_untouched(
    admin_client: APIClient,
    environment: Environment,
    multivariate_feature: Feature,
    other_mv_value: MultivariateFeatureStateValue,
    url: str,
    feature_state_value: Any,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment, feature=multivariate_feature
    )
    own_values = list(feature_state.multivariate_feature_state_values.all())
    other_feature_state_id = other_mv_value.feature_state_id

    # When
    response = admin_client.put(
        url.format(api_key=environment.api_key, id=feature_state.id),
        data=json.dumps(
            {
                "feature": multivariate_feature.id,
                "environment": environment.id,
                "enabled": True,
                "feature_state_value": feature_state_value,
                "multivariate_feature_state_values": [
                    {
                        "id": value.id,
                        "multivariate_feature_option": value.multivariate_feature_option_id,
                        "percentage_allocation": 20,
                    }
                    for value in own_values
                ]
                + [
                    {
                        "id": other_mv_value.id,
                        "multivariate_feature_option": other_mv_value.multivariate_feature_option_id,
                        "percentage_allocation": 1,
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    other_mv_value.refresh_from_db()
    assert other_mv_value.feature_state_id == other_feature_state_id
    assert other_mv_value.percentage_allocation != 1


def test_update_metadata_model_field__other_organisation_requirement_id__leaves_it_untouched(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
    other_project: Project,
) -> None:
    # Given
    project_type = ContentType.objects.get_for_model(Project)
    feature_type = ContentType.objects.get_for_model(Feature)
    other_requirement = MetadataModelFieldRequirement.objects.create(
        model_field=MetadataModelField.objects.create(
            field=MetadataField.objects.create(
                name="other", type="str", organisation=other_project.organisation
            ),
            content_type=feature_type,
        ),
        content_type=project_type,
        object_id=other_project.id,
    )
    other_model_field_id = other_requirement.model_field_id
    field = MetadataField.objects.create(
        name="mine", type="str", organisation=organisation
    )
    model_field = MetadataModelField.objects.create(
        field=field, content_type=feature_type
    )

    # When
    response = admin_client.put(
        f"/api/v1/organisations/{organisation.id}/metadata-model-fields/{model_field.id}/",
        data=json.dumps(
            {
                "field": field.id,
                "content_type": feature_type.id,
                "is_required_for": [
                    {
                        "id": other_requirement.id,
                        "content_type": project_type.id,
                        "object_id": project.id,
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    other_requirement.refresh_from_db()
    assert (other_requirement.model_field_id, other_requirement.object_id) == (
        other_model_field_id,
        other_project.id,
    )
    assert model_field.is_required_for.get().object_id == project.id


def test_create_version_feature_state__other_project_feature_segment_and_multivariate_value_ids__leaves_them_untouched(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    other_mv_value: MultivariateFeatureStateValue,
) -> None:
    # Given
    other_feature_state = other_mv_value.feature_state
    other_feature_segment = FeatureSegment.objects.create(
        feature=other_feature_state.feature,
        segment=Segment.objects.create(
            name="other", project=other_feature_state.feature.project
        ),
        environment=other_feature_state.environment,
    )
    other_feature_segment_before = (
        other_feature_segment.environment_id,
        other_feature_segment.feature_id,
        other_feature_segment.segment_id,
    )
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_v2_versioning.id}/features/{feature.id}"
        f"/versions/{version.uuid}/featurestates/",
        data=json.dumps(
            {
                "enabled": True,
                "feature_state_value": {"type": "unicode", "string_value": "x"},
                "feature_segment": {
                    "id": other_feature_segment.id,
                    "segment": segment.id,
                    "priority": 0,
                },
                "multivariate_feature_state_values": [
                    {
                        "id": other_mv_value.id,
                        "multivariate_feature_option": other_mv_value.multivariate_feature_option_id,
                        "percentage_allocation": 1,
                    }
                ],
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 201
    other_feature_segment.refresh_from_db()
    other_mv_value.refresh_from_db()
    assert (
        other_feature_segment.environment_id,
        other_feature_segment.feature_id,
        other_feature_segment.segment_id,
    ) == other_feature_segment_before
    assert other_mv_value.feature_state == other_feature_state
    assert response.json()["feature_segment"]["id"] != other_feature_segment.id


def test_create_version_feature_state__form_encoded_other_project_feature_segment_id__leaves_it_untouched(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    other_project: Project,
) -> None:
    # Given
    other_environment = Environment.objects.create(name="Other", project=other_project)
    other_feature_segment = FeatureSegment.objects.create(
        feature=Feature.objects.create(name="other", project=other_project),
        segment=Segment.objects.create(name="other", project=other_project),
        environment=other_environment,
    )
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_v2_versioning.id}/features/{feature.id}"
        f"/versions/{version.uuid}/featurestates/",
        data={
            "enabled": True,
            "feature_state_value.type": "unicode",
            "feature_state_value.string_value": "x",
            "feature_segment.id": other_feature_segment.id,
            "feature_segment.segment": segment.id,
            "feature_segment.priority": 0,
        },
    )

    # Then
    assert response.status_code == 201
    other_feature_segment.refresh_from_db()
    assert other_feature_segment.environment == other_environment
    assert response.json()["feature_segment"]["id"] != other_feature_segment.id


def test_update_version_feature_state__own_feature_segment_id_as_padded_string__updates_it_in_place(
    admin_client: APIClient,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    url = (
        f"/api/v1/environments/{environment_v2_versioning.id}/features/{feature.id}"
        f"/versions/{version.uuid}/featurestates/"
    )
    created = admin_client.post(
        url,
        data=json.dumps(
            {
                "enabled": True,
                "feature_state_value": {"type": "unicode", "string_value": "x"},
                "feature_segment": {"segment": segment.id, "priority": 0},
            }
        ),
        content_type="application/json",
    ).json()
    feature_segment_id = created["feature_segment"]["id"]

    # When
    response = admin_client.put(
        f"{url}{created['id']}/",
        data=json.dumps(
            {
                "enabled": False,
                "feature_state_value": {"type": "unicode", "string_value": "y"},
                "feature_segment": {
                    "id": f"0{feature_segment_id}",
                    "segment": segment.id,
                    "priority": 1,
                },
            }
        ),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    assert response.json()["feature_segment"]["id"] == feature_segment_id
    assert FeatureSegment.objects.get(id=feature_segment_id).priority == 1


@pytest.mark.parametrize(
    "pk, obj, expected",
    [
        ("42", FeatureSegment(id=42), True),
        ("042", FeatureSegment(id=42), True),
        ("43", FeatureSegment(id=42), False),
        ("not-a-pk", FeatureSegment(id=42), False),
        (None, FeatureSegment(id=42), False),
        ("42", None, False),
    ],
)
def test_is_pk_of__given_pk__returns_whether_it_refers_to_obj(
    pk: str | None, obj: FeatureSegment | None, expected: bool
) -> None:
    # Given
    model = FeatureSegment

    # When
    result = _is_pk_of(model, pk, obj)

    # Then
    assert result is expected
