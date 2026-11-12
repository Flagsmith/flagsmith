import pytest

from integrations.gitlab.services.url_parsing import (
    parse_project_path,
    parse_resource_iid,
)


@pytest.mark.parametrize(
    "url, expected_path",
    [
        ("https://gitlab.example.com/testorg/testrepo/-/issues/42", "testorg/testrepo"),
        (
            "https://gitlab.example.com/testorg/testrepo/-/work_items/99",
            "testorg/testrepo",
        ),
        (
            "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
            "testorg/testrepo",
        ),
        ("https://gitlab.example.com/org/sub/repo/-/issues/1", "org/sub/repo"),
    ],
    ids=["issue", "work_item", "merge_request", "nested_group"],
)
def test_parse_project_path__valid_url__returns_path(
    url: str, expected_path: str
) -> None:
    # Given / When
    result = parse_project_path(url)

    # Then
    assert result == expected_path


@pytest.mark.parametrize(
    "url",
    [None, "", "https://gitlab.example.com/not-a-resource"],
    ids=["none", "empty", "unparseable"],
)
def test_parse_project_path__invalid_input__returns_none(url: str | None) -> None:
    # Given / When
    result = parse_project_path(url)

    # Then
    assert result is None


@pytest.mark.parametrize(
    "url, expected_iid",
    [
        ("https://gitlab.example.com/testorg/testrepo/-/issues/42", 42),
        ("https://gitlab.example.com/testorg/testrepo/-/work_items/99", 99),
        ("https://gitlab.example.com/testorg/testrepo/-/merge_requests/7", 7),
        ("https://gitlab.example.com/org/sub/repo/-/issues/1", 1),
    ],
    ids=["issue", "work_item", "merge_request", "nested_group"],
)
def test_parse_resource_iid__valid_url__returns_iid(
    url: str, expected_iid: int
) -> None:
    # Given / When
    result = parse_resource_iid(url)

    # Then
    assert result == expected_iid


@pytest.mark.parametrize(
    "url",
    [None, "", "https://gitlab.example.com/not-a-resource"],
    ids=["none", "empty", "unparseable"],
)
def test_parse_resource_iid__invalid_input__returns_none(url: str | None) -> None:
    # Given / When
    result = parse_resource_iid(url)

    # Then
    assert result is None
