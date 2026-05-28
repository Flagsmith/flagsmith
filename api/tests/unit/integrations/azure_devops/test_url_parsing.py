import pytest

from integrations.azure_devops.services.url_parsing import (
    AdoPullRequestRef,
    AdoWorkItemRef,
    parse_pull_request_url,
    parse_work_item_url,
)


@pytest.mark.parametrize(
    "url, expected",
    [
        # Cloud, plain
        (
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42",
            AdoPullRequestRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                repository="repo",
                pull_request_id=42,
            ),
        ),
        # Cloud, with trailing slash
        (
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42/",
            AdoPullRequestRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                repository="repo",
                pull_request_id=42,
            ),
        ),
        # Cloud, with query string
        (
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42?_a=overview",
            AdoPullRequestRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                repository="repo",
                pull_request_id=42,
            ),
        ),
        # Cloud, project name with spaces (URL-encoded)
        (
            "https://dev.azure.com/test-org/My%20Project/_git/my-repo/pullrequest/7",
            AdoPullRequestRef(
                organisation_root="https://dev.azure.com/test-org",
                project="My Project",
                repository="my-repo",
                pull_request_id=7,
            ),
        ),
        # On-prem with a collection segment
        (
            "https://devops.internal.example.com/DefaultCollection/proj/_git/repo/pullrequest/100",
            AdoPullRequestRef(
                organisation_root="https://devops.internal.example.com/DefaultCollection",
                project="proj",
                repository="repo",
                pull_request_id=100,
            ),
        ),
    ],
)
def test_parse_pull_request_url__valid_shapes__returns_ref(
    url: str, expected: AdoPullRequestRef
) -> None:
    # Given
    target_url = url

    # When
    result = parse_pull_request_url(target_url)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://github.com/foo/bar/pull/42",
        "https://gitlab.com/foo/bar/-/merge_requests/42",
        "https://dev.azure.com/test-org/proj/_git/repo",
        "https://dev.azure.com/test-org/proj/_workitems/edit/42",
        "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/not-a-number",
    ],
)
def test_parse_pull_request_url__malformed_or_other_shapes__returns_none(
    url: str,
) -> None:
    # Given
    target_url = url

    # When
    result = parse_pull_request_url(target_url)

    # Then
    assert result is None


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "https://dev.azure.com/test-org/proj/_workitems/edit/100",
            AdoWorkItemRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                work_item_id=100,
            ),
        ),
        (
            "https://dev.azure.com/test-org/proj/_workitems/edit/100/",
            AdoWorkItemRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                work_item_id=100,
            ),
        ),
        (
            "https://dev.azure.com/test-org/My%20Project/_workitems/edit/7",
            AdoWorkItemRef(
                organisation_root="https://dev.azure.com/test-org",
                project="My Project",
                work_item_id=7,
            ),
        ),
        (
            "https://devops.internal.example.com/DefaultCollection/proj/_workitems/edit/100",
            AdoWorkItemRef(
                organisation_root="https://devops.internal.example.com/DefaultCollection",
                project="proj",
                work_item_id=100,
            ),
        ),
    ],
)
def test_parse_work_item_url__valid_shapes__returns_ref(
    url: str, expected: AdoWorkItemRef
) -> None:
    # Given
    target_url = url

    # When
    result = parse_work_item_url(target_url)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://github.com/foo/bar/issues/42",
        "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42",
        "https://dev.azure.com/test-org/proj/_workitems/edit/not-a-number",
    ],
)
def test_parse_work_item_url__malformed_or_other_shapes__returns_none(
    url: str,
) -> None:
    # Given
    target_url = url

    # When
    result = parse_work_item_url(target_url)

    # Then
    assert result is None
