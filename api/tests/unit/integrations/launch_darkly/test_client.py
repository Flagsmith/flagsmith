import json
from typing import Any

import pytest
from pytest_mock import MockerFixture
from requests import HTTPError
from requests_mock import Mocker as RequestsMockerFixture

from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.exceptions import LaunchDarklyRateLimitError


def test_launch_darkly_client__get_project__return_expected(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20240415"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )

    example_response_content = (
        request.path.parent / "example_api_responses/getProject.json"
    ).read_text()

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
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20240415"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE",
        new=1,
    )

    example_response_1_content = (
        request.path.parent / "example_api_responses/getEnvironmentsByProject_1.json"
    ).read_text()
    example_response_2_content = (
        request.path.parent / "example_api_responses/getEnvironmentsByProject_2.json"
    ).read_text()

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
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20240415"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_FLAGS_LIMIT_PER_PAGE",
        new=3,
    )

    example_response_1_content = (
        request.path.parent / "example_api_responses/getFeatureFlags_1.json"
    ).read_text()
    example_response_2_content = (
        request.path.parent / "example_api_responses/getFeatureFlags_2.json"
    ).read_text()

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
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"
    api_version = "20240415"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/flags/test-project-key?limit=1",
        text=(
            request.path.parent / "example_api_responses/getFeatureFlags_1.json"
        ).read_text(),
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    expected_result = 5

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flag_count(project_key=project_key)

    # Then
    assert result == expected_result


def test_launch_darkly_client__get_flag_tags__return_expected(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    api_version = "20240415"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/tags?kind=flag",
        text=(request.path.parent / "example_api_responses/getTags.json").read_text(),
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    expected_result = ["testtag", "testtag2"]

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flag_tags()

    # Then
    assert result == expected_result


@pytest.mark.parametrize(
    "response_headers",
    [{"Retry-After": "0.1"}, {"X-Ratelimit-Reset": "1672531200100"}],
)
@pytest.mark.freeze_time("2023-01-01T00:00:00Z")
def test_launch_darkly_client__rate_limit__expected_backoff(
    request: pytest.FixtureRequest,
    requests_mock: RequestsMockerFixture,
    response_headers: dict[str, str],
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    example_response_content = (
        request.path.parent / "example_api_responses/getProject.json"
    ).read_text()

    expected_result = json.loads(example_response_content)

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key",
        [
            {"status_code": 429, "headers": response_headers},
            {"status_code": 429, "headers": response_headers},
            {"status_code": 200, "text": example_response_content},
        ],
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_project(project_key=project_key)

    # Then
    assert result == expected_result


@pytest.mark.parametrize(
    "response_headers",
    [{"Retry-After": "0.1"}, {"X-Ratelimit-Reset": "1672531200100"}],
)
@pytest.mark.freeze_time("2023-01-01T00:00:00Z")
def test_launch_darkly_client__rate_limit_max_retries__raises_expected(
    requests_mock: RequestsMockerFixture,
    response_headers: dict[str, str],
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key",
        [
            {"status_code": 429, "headers": response_headers},
            {"status_code": 429, "headers": response_headers},
            {"status_code": 429, "headers": response_headers},
            {"status_code": 429, "headers": response_headers},
            {"status_code": 429, "headers": response_headers},
        ],
    )

    client = LaunchDarklyClient(token=token)

    # When & Then
    with pytest.raises(LaunchDarklyRateLimitError) as exc_info:
        client.get_project(project_key=project_key)

    assert exc_info.value.retry_at.isoformat() == "2023-01-01T00:00:00.100000+00:00"


def test_launch_darkly_client__invalid_response__raises_expected(
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key",
        status_code=404,
    )

    client = LaunchDarklyClient(token=token)

    # When & Then
    with pytest.raises(HTTPError):
        client.get_project(project_key=project_key)


def test_launch_darkly_client__rate_limit_invalid_response__raises_expected(
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key",
        [
            {"status_code": 429, "headers": {"Retry-After": "0.1"}},
            {"status_code": 429, "headers": {"Retry-After": "0.1"}},
            {"status_code": 429, "headers": {"Retry-After": "0.1"}},
            {"status_code": 429, "headers": {"Retry-After": "0.1"}},
            {"status_code": 404},
        ],
    )

    client = LaunchDarklyClient(token=token)

    # When & Then
    with pytest.raises(HTTPError):
        client.get_project(project_key=project_key)


def test_launch_darkly_client__rate_limit_no_headers__waits_expected(
    request: pytest.FixtureRequest,
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-key"

    mocker.patch(
        "integrations.launch_darkly.client.BACKOFF_DEFAULT_RETRY_AFTER_SECONDS",
        new=0.1,
    )

    example_response_content = (
        request.path.parent / "example_api_responses/getProject.json"
    ).read_text()
    expected_result = json.loads(example_response_content)

    requests_mock.get(
        "https://app.launchdarkly.com/api/v2/projects/test-project-key",
        [
            {"status_code": 429},
            {"status_code": 200, "text": example_response_content},
        ],
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_project(project_key=project_key)

    # Then
    assert result == expected_result


def test_launch_darkly_client__get_flags_with_env_keys__return_expected(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-env-keys"
    api_version = "20240415"
    environment_keys = ["production", "test"]

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_FLAGS_LIMIT_PER_PAGE",
        100,
    )

    response_data = {
        "items": [
            {
                "key": "test-flag",
                "name": "Test Flag",
                "kind": "boolean",
                "environments": {
                    "production": {"on": True},
                    "test": {"on": False},
                },
            }
        ],
        "totalCount": 1,
    }

    requests_mock.get(
        f"https://app.launchdarkly.com/api/v2/flags/{project_key}",
        json=response_data,
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flags(
        project_key=project_key,
        environment_keys=environment_keys,
    )

    # Then
    assert result == response_data["items"]
    assert "env=production" in requests_mock.request_history[0].url
    assert "env=test" in requests_mock.request_history[0].url


def test_launch_darkly_client__get_flags_with_env_keys_batching__merges_environments(
    mocker: MockerFixture,
    requests_mock: RequestsMockerFixture,
) -> None:
    # Given
    token = "test-token"
    project_key = "test-project-batching"
    api_version = "20240415"
    environment_keys = ["env1", "env2", "env3", "env4"]

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_FLAGS_LIMIT_PER_PAGE",
        100,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_ENV_FILTER_MAX",
        3,
    )

    batch1_response = {
        "items": [
            {
                "key": "flag1",
                "environments": {
                    "env1": {"on": True},
                    "env2": {"on": False},
                    "env3": {"on": True},
                },
            }
        ],
        "totalCount": 1,
    }

    batch2_response = {
        "items": [
            {
                "key": "flag1",
                "environments": {
                    "env4": {"on": False},
                },
            }
        ],
        "totalCount": 1,
    }

    requests_mock.get(
        f"https://app.launchdarkly.com/api/v2/flags/{project_key}",
        [
            {"json": batch1_response},
            {"json": batch2_response},
        ],
        request_headers={"Authorization": token, "LD-API-Version": api_version},
    )

    client = LaunchDarklyClient(token=token)

    # When
    result = client.get_flags(
        project_key=project_key,
        environment_keys=environment_keys,
    )

    # Then
    assert len(result) == 1
    assert result[0]["key"] == "flag1"
    environments: Any = result[0]["environments"]
    assert environments == {
        "env1": {"on": True},
        "env2": {"on": False},
        "env3": {"on": True},
        "env4": {"on": False},
    }

    assert len(requests_mock.request_history) == 2
