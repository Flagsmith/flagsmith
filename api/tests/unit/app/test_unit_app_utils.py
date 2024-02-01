import json
import pathlib
from unittest import mock

from pytest_mock import MockerFixture

from app.utils import get_version_info


def test_get_version_info(mocker: MockerFixture) -> None:
    # Given
    mocked_pathlib = mocker.patch("app.utils.pathlib")

    def path_side_effect(file_path: str) -> mocker.MagicMock:
        mocked_path_object = mocker.MagicMock(spec=pathlib.Path)

        if file_path == "./ENTERPRISE_VERSION":
            mocked_path_object.exists.return_value = True

        if file_path == "./SAAS_DEPLOYMENT":
            mocked_path_object.exists.return_value = False

        return mocked_path_object

    mocked_pathlib.Path.side_effect = path_side_effect

    manifest_mocked_file = {
        ".": "2.66.2",
    }
    mock_get_file_contents = mocker.patch("app.utils._get_file_contents")
    mock_get_file_contents.side_effect = (json.dumps(manifest_mocked_file), "some_sha")

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "some_sha",
        "image_tag": "2.66.2",
        "is_enterprise": True,
        "is_saas": False,
        "package_versions": {".": "2.66.2"},
    }


def test_get_version_info_with_missing_files(mocker: MockerFixture) -> None:
    # Given
    mocked_pathlib = mocker.patch("app.utils.pathlib")

    def path_side_effect(file_path: str) -> mocker.MagicMock:
        mocked_path_object = mocker.MagicMock(spec=pathlib.Path)

        if file_path == "./ENTERPRISE_VERSION":
            mocked_path_object.exists.return_value = True

        if file_path == "./SAAS_DEPLOYMENT":
            mocked_path_object.exists.return_value = False

        return mocked_path_object

    mocked_pathlib.Path.side_effect = path_side_effect
    mock.mock_open.side_effect = IOError

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "is_enterprise": True,
        "is_saas": False,
    }
