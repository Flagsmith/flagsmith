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
