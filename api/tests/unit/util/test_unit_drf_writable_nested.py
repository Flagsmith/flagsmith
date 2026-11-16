import json
from typing import Any

import pytest
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from metadata.models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from organisations.models import Organisation
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule


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


def _put(client: APIClient, url: str, data: dict[str, Any]) -> Any:
    return client.put(url, data=json.dumps(data), content_type="application/json")


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
    response = _put(
        admin_client,
        f"/api/v1/projects/{project.id}/segments/{segment.id}/",
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
        },
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
    response = _put(
        admin_client,
        f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/",
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
        },
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
    response = _put(
        admin_client,
        url.format(api_key=environment.api_key, id=feature_state.id),
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
        },
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
    response = _put(
        admin_client,
        f"/api/v1/organisations/{organisation.id}/metadata-model-fields/{model_field.id}/",
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
        },
    )

    # Then
    assert response.status_code == 200
    other_requirement.refresh_from_db()
    assert (other_requirement.model_field_id, other_requirement.object_id) == (
        other_model_field_id,
        other_project.id,
    )
    assert model_field.is_required_for.get().object_id == project.id
