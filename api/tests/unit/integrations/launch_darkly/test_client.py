import json

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
    api_version = "20230101"

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
    api_version = "20230101"

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
    api_version = "20230101"

    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_VERSION",
        new=api_version,
    )
    mocker.patch(
        "integrations.launch_darkly.client.LAUNCH_DARKLY_API_ITEM_COUNT_LIMIT_PER_PAGE",
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
    api_version = "20230101"

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
    api_version = "20230101"

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
