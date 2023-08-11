import json
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

    manifest_mocked_file = {
        ".": "2.66.2",
        "frontend": "2.66.2",
        "api": "2.66.2",
        "docs": "2.66.2",
    }
    mock_is_file = mocker.patch("os.path.isfile")
    mock_is_file.side_effect = (True,)
    mock_get_file_contents = mocker.patch("app.utils._get_file_contents")
    mock_get_file_contents.side_effect = (json.dumps(manifest_mocked_file), "some_sha")

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "some_sha",
        "image_tag": "2.66.2",
        "is_enterprise": True,
        "package_versions": {
            ".": "2.66.2",
            "api": "2.66.2",
            "docs": "2.66.2",
            "frontend": "2.66.2",
        },
    }
