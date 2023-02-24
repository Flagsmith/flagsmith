import pytest

from projects.models import Project


@pytest.mark.parametrize(
    "feature_name_regex, feature_name, expected_result",
    (
        ("[a-z]+", "validfeature", True),
        ("[a-z]+", "InvalidFeature", False),
        ("^[a-z]+$", "validfeature", True),
        ("^[a-z]+$", "InvalidFeature", False),
    ),
)
def test_is_feature_name_valid(feature_name_regex, feature_name, expected_result):
    assert (
        Project(
            name="test", feature_name_regex=feature_name_regex
        ).is_feature_name_valid(feature_name)
        == expected_result
    )


def test_updating_project_clears_environment_caches(environment, project, mocker):
    # Given
    mock_environment_cache = mocker.patch("projects.models.environment_cache")

    # When
    project.name += "update"
    project.save()

    # Then
    mock_environment_cache.delete_many.assert_called_once_with([environment.api_key])


def test_environments_are_updated_in_dynamodb_when_project_id_updated(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mocker,
):
    # Given
    mock_environments_wrapper = mocker.patch("environments.models.environment_wrapper")

    # When
    dynamo_enabled_project.name = dynamo_enabled_project.name + " updated"
    dynamo_enabled_project.save()

    # Then
    mock_environments_wrapper.write_environments.assert_called_once_with(
        [dynamo_enabled_project_environment_one, dynamo_enabled_project_environment_two]
    )
