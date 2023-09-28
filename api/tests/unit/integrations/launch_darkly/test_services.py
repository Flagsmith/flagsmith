from typing import Type
from unittest.mock import MagicMock

import pytest
from django.core import signing
from requests.exceptions import HTTPError, Timeout

from environments.models import Environment
from features.models import Feature, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from features.value_types import STRING
from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import (
    create_import_request,
    process_import_request,
)
from projects.models import Project
from users.models import FFAdminUser


def test_create_import_request__return_expected(
    ld_client_mock: MagicMock,
    ld_client_class_mock: MagicMock,
    project: Project,
    test_user: FFAdminUser,
) -> None:
    # Given
    ld_project_key = "test-project-key"
    ld_token = "test-token"

    # When
    result = create_import_request(
        project=project,
        user=test_user,
        ld_project_key=ld_project_key,
        ld_token=ld_token,
    )

    # Then
    ld_client_class_mock.assert_called_once_with(ld_token)
    ld_client_mock.get_project.assert_called_once_with(project_key=ld_project_key)
    ld_client_mock.get_flag_count.assert_called_once_with(project_key=ld_project_key)

    assert result.status == {
        "requested_environment_count": 2,
        "requested_flag_count": 5,
    }
    assert signing.loads(result.ld_project_key, salt="ldimport") == ld_project_key
    assert signing.loads(result.ld_token, salt="ldimport") == ld_token
    assert result.created_by == test_user
    assert result.project == project


@pytest.mark.parametrize(
    "failing_ld_client_method_name", ["get_environments", "get_flags", "get_flag_tags"]
)
@pytest.mark.parametrize(
    "exception, expected_error_message",
    [
        (
            HTTPError(response=MagicMock(status_code=503)),
            "HTTP 503 when requesting LaunchDarkly",
        ),
        (Timeout(), "Timeout when requesting LaunchDarkly"),
    ],
)
def test_process_import_request__api_error__expected_status(
    ld_client_mock: MagicMock,
    ld_client_class_mock: MagicMock,
    failing_ld_client_method_name: str,
    exception: Type[Exception],
    expected_error_message: str,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given
    getattr(ld_client_mock, failing_ld_client_method_name).side_effect = exception

    # When
    with pytest.raises(type(exception)):
        process_import_request(import_request)

    # Then
    assert import_request.completed_at
    assert import_request.ld_token == ""
    assert import_request.ld_project_key == ""
    assert import_request.status["result"] == "failure"
    assert import_request.status["error_message"] == expected_error_message


def test_process_import_request__success__expected_status(
    project: Project,
    import_request: LaunchDarklyImportRequest,
):
    # When
    process_import_request(import_request)

    # Then
    # Import request is marked as completed successfully.
    assert import_request.completed_at
    assert import_request.ld_token == ""
    assert import_request.ld_project_key == ""
    assert import_request.status["result"] == "success"

    # Environment names are correct.
    assert list(
        Environment.objects.filter(project=project).values_list("name", flat=True)
    ) == ["Test", "Production"]

    # Feature names are correct.
    assert list(
        Feature.objects.filter(project=project).values_list("name", flat=True)
    ) == ["flag1", "flag2_value", "flag3_multivalue", "flag4_multivalue", "flag5"]

    # Standard feature states have expected values.
    boolean_standard_feature = Feature.objects.get(project=project, name="flag1")
    boolean_standard_feature_states_by_env_name = {
        fs.environment.name: fs
        for fs in FeatureState.objects.filter(feature=boolean_standard_feature)
    }
    boolean_standard_feature_states_by_env_name["Test"].enabled is True
    boolean_standard_feature_states_by_env_name["Production"].enabled is False

    value_standard_feature = Feature.objects.get(project=project, name="flag2_value")
    value_standard_feature_states_by_env_name = {
        fs.environment.name: fs
        for fs in FeatureState.objects.filter(feature=value_standard_feature)
    }
    value_standard_feature_states_by_env_name["Test"].enabled is True
    value_standard_feature_states_by_env_name[
        "Test"
    ].get_feature_state_value() == "123123"
    value_standard_feature_states_by_env_name["Production"].enabled is False
    value_standard_feature_states_by_env_name[
        "Production"
    ].get_feature_state_value() == ""

    # Multivariate feature states with percentage rollout have expected values.
    percentage_mv_feature = Feature.objects.get(
        project=project, name="flag4_multivalue"
    )
    percentage_mv_options = list(
        MultivariateFeatureOption.objects.filter(feature=percentage_mv_feature)
    )
    assert set(option.type for option in percentage_mv_options) == {STRING}
    assert [option.string_value for option in percentage_mv_options] == [
        "variation3",
        "variation2",
        "variation1",
    ]

    # Multivariate feature states are set correctly.
    percentage_mv_feature_states_by_env_name = {
        fs.environment.name: fs
        for fs in FeatureState.objects.filter(feature=percentage_mv_feature)
    }
    assert percentage_mv_feature_states_by_env_name["Test"].enabled is False
    assert (
        percentage_mv_feature_states_by_env_name["Test"]
        .get_multivariate_feature_state_value("test")
        .string_value
        == "variation1"
    )
    assert percentage_mv_feature_states_by_env_name["Production"].enabled is True
    assert (
        percentage_mv_feature_states_by_env_name["Production"]
        .get_multivariate_feature_state_value("test")
        .string_value
        == "variation2"
    )

    # Multivariate feature states with percentage rollout have correct percentage
    # allocations.
    assert (
        sum(
            mvfs.percentage_allocation
            for mvfs in MultivariateFeatureStateValue.objects.filter(
                feature_state=percentage_mv_feature_states_by_env_name["Test"]
            )
        )
        == 100
    )
    assert (
        sum(
            mvfs.percentage_allocation
            for mvfs in MultivariateFeatureStateValue.objects.filter(
                feature_state=percentage_mv_feature_states_by_env_name["Production"]
            )
        )
        == 100
    )

    # Tags are imported correctly.
    tagged_feature = Feature.objects.get(project=project, name="flag5")
    [tag.label for tag in tagged_feature.tags.all()] == ["testtag", "testtag2"]
