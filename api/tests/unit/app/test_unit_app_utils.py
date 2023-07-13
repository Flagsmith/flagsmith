import pathlib

from pytest_mock import MockerFixture

from app.utils import get_version_info


def test_get_version_info(mocker: MockerFixture) -> None:
    # Given
    mocked_pathlib = mocker.patch("app.utils.pathlib")

    def path_side_effect(file_path: str) -> mocker.MagicMock:
        mocked_path_object = mocker.MagicMock(spec=pathlib.Path)

        if file_path == "./ENTERPRISE_VERSION":
            mocked_path_object.exists.return_value = True

        return mocked_path_object

    mocked_pathlib.Path.side_effect = path_side_effect

    mock_get_file_contents = mocker.patch("app.utils._get_file_contents")
    mock_get_file_contents.side_effect = ("some_sha", "v1.0.0")

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "some_sha",
        "image_tag": "v1.0.0",
        "is_enterprise": True,
    }
