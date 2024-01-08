import json
from os.path import abspath, dirname, join

from pytest_mock import MockerFixture
from requests_mock import Mocker as RequestsMockerFixture

from integrations.launch_darkly.client import LaunchDarklyClient


def test_launch_darkly_client__get_project__return_expected(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20230101"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )

    example_response_file_path = join(
        dirname(abspath(__file__)), "example_api_responses/getProject.json"
    )
    with open(example_response_file_path) as example_response_fp:
        example_response_content = example_response_fp.read()

    expected_result = json.loads(example_response_content)

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key",
        text=example_response_content,
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_project(project_key=project_key)

    # Then
    assert result == expected_result


def test_launch_darkly_client__get_environments__return_expected(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20230101"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE",
        new=1,
    )

    example_response_1_file_path = join(
        dirname(abspath(__file__)),
        "example_api_responses/getEnvironmentsByProject_1.json",
    )
    example_response_2_file_path = join(
        dirname(abspath(__file__)),
        "example_api_responses/getEnvironmentsByProject_2.json",
    )
    with open(example_response_1_file_path) as example_response_1_fp:
        example_response_1_content = example_response_1_fp.read()
    with open(example_response_2_file_path) as example_response_2_fp:
        example_response_2_content = example_response_2_fp.read()

    expected_result = [
        *json.loads(example_response_1_content)["items"],
        *json.loads(example_response_2_content)["items"],
    ]

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key/environments?limit=1",
        text=example_response_1_content,
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )
    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key/environments?limit=1&offset=1",
        text=example_response_2_content,
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_environments(project_key=project_key)

    # Then
    assert result == expected_result


def test_launch_darkly_client__get_flags__return_expected(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20230101"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE",
        new=3,
    )

    example_response_1_file_path = join(
        dirname(abspath(__file__)),
        "example_api_responses/getFeatureFlags_1.json",
    )
    example_response_2_file_path = join(
        dirname(abspath(__file__)),
        "example_api_responses/getFeatureFlags_2.json",
    )
    with open(example_response_1_file_path) as example_response_1_fp:
        example_response_1_content = example_response_1_fp.read()
    with open(example_response_2_file_path) as example_response_2_fp:
        example_response_2_content = example_response_2_fp.read()

    expected_result = [
        *json.loads(example_response_1_content)["items"],
        *json.loads(example_response_2_content)["items"],
    ]

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/flags/test-project-key?limit=3",
        text=example_response_1_content,
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )
    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/flags/test-project-key?limit=3&offset=3&summary=true",
        text=example_response_2_content,
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flags(project_key=project_key)

    # Then
    assert result == expected_result


def test_launch_darkly_client__get_flag_count__return_expected(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20230101"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )

    example_response_file_path = join(
        dirname(abspath(__file__)),
        "example_api_responses/getFeatureFlags_1.json",
    )
    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/flags/test-project-key?limit=1",
        text=open(example_response_file_path).read(),
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    expected_result = 5

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flag_count(project_key=project_key)

    # Then
    assert result == expected_result


def test_launch_darkly_client__get_flag_tags__return_expected(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    api_version = "20230101"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )

    example_response_file_path = join(
        dirname(abspath(__file__)),
        "example_api_responses/getTags.json",
    )
    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/tags?kind=flag",
        text=open(example_response_file_path).read(),
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    expected_result = ["testtag", "testtag2"]

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flag_tags()

    # Then
    assert result == expected_result
