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
