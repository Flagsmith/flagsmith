import pytest
import requests as _requests
import responses
from requests.exceptions import HTTPError
from responses.matchers import header_matcher, query_param_matcher

from integrations.gitlab.client import (
    _build_paginated_response,
    create_flagsmith_flag_label,
    create_gitlab_issue,
    fetch_gitlab_project_members,
    fetch_gitlab_projects,
    fetch_search_gitlab_resource,
    get_gitlab_resource_metadata,
    label_gitlab_resource,
    post_comment_to_gitlab,
)
from integrations.gitlab.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    ProjectQueryParams,
)
from integrations.gitlab.types import GitLabProject

INSTANCE_URL = "https://gitlab.example.com"
ACCESS_TOKEN = "test-access-token"
EXPECTED_HEADERS = {"PRIVATE-TOKEN": ACCESS_TOKEN}


@responses.activate
def test_fetch_gitlab_projects__valid_token__returns_projects() -> None:
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects",
        json=[
            {"id": 1, "name": "my-project", "path_with_namespace": "group/my-project"},
            {"id": 2, "name": "other", "path_with_namespace": "group/other"},
        ],
        match=[
            header_matcher(EXPECTED_HEADERS),
            query_param_matcher({"membership": "true", "per_page": "20", "page": "1"}),
        ],
        status=200,
    )
    params = PaginatedQueryParams(page=1, page_size=20)

    # When
    result = fetch_gitlab_projects(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert len(result["results"]) == 2
    assert result["results"][0] == {
        "id": 1,
        "name": "my-project",
        "path_with_namespace": "group/my-project",
    }


@responses.activate
def test_fetch_search_gitlab_resource__issues__returns_results() -> None:
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects/1/issues",
        json=[
            {
                "id": 10,
                "iid": 5,
                "title": "Bug fix",
                "state": "opened",
                "web_url": f"{INSTANCE_URL}/group/project/-/issues/5",
            },
        ],
        match=[header_matcher(EXPECTED_HEADERS)],
        status=200,
        headers={"x-total": "1"},
    )
    params = IssueQueryParams(gitlab_project_id=1, project_name="group/project")

    # When
    result = fetch_search_gitlab_resource(
        resource_type="issues",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    results = result["results"]
    assert len(results) == 1
    resource = results[0]
    assert resource["title"] == "Bug fix"  # type: ignore[typeddict-item]
    assert resource["merged"] is False  # type: ignore[typeddict-item]
    assert resource["draft"] is False  # type: ignore[typeddict-item]


@responses.activate
def test_fetch_search_gitlab_resource__merge_requests__returns_mr_fields() -> None:
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects/1/merge_requests",
        json=[
            {
                "id": 20,
                "iid": 3,
                "title": "Add feature",
                "state": "merged",
                "web_url": f"{INSTANCE_URL}/group/project/-/merge_requests/3",
                "merged_at": "2025-01-01T00:00:00Z",
                "draft": False,
            },
        ],
        match=[header_matcher(EXPECTED_HEADERS)],
        status=200,
        headers={"x-total": "1"},
    )
    params = IssueQueryParams(gitlab_project_id=1, project_name="group/project")

    # When
    result = fetch_search_gitlab_resource(
        resource_type="merge_requests",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    results = result["results"]
    assert len(results) == 1
    resource = results[0]
    assert resource["merged"] is True  # type: ignore[typeddict-item]
    assert resource["draft"] is False  # type: ignore[typeddict-item]


@pytest.mark.parametrize(
    "filter_field,filter_value,expected_param",
    [
        ("search_text", "my search", "search"),
        ("author", "jdoe", "author_username"),
        ("assignee", "jsmith", "assignee_username"),
    ],
)
@responses.activate
def test_fetch_search_gitlab_resource__with_filter__appends_query_param(
    filter_field: str,
    filter_value: str,
    expected_param: str,
) -> None:
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects/1/issues",
        json=[],
        status=200,
        headers={"x-total": "0"},
    )
    params = IssueQueryParams(
        gitlab_project_id=1,
        project_name="group/project",
        **{filter_field: filter_value},  # type: ignore[arg-type]
    )

    # When
    fetch_search_gitlab_resource(
        resource_type="issues",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert len(responses.calls) == 1
    request_url = responses.calls[0].request.url or ""  # type: ignore[union-attr]
    assert f"{expected_param}=" in request_url


@responses.activate
def test_fetch_gitlab_project_members__happy_path__returns_members() -> None:
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects/1/members",
        json=[
            {
                "username": "jdoe",
                "avatar_url": "https://gitlab.example.com/avatar/jdoe",
                "name": "John Doe",
            }
        ],
        match=[header_matcher(EXPECTED_HEADERS)],
        status=200,
        headers={"x-page": "1", "x-total-pages": "1"},
    )
    params = ProjectQueryParams(gitlab_project_id=1, project_name="group/project")

    # When
    result = fetch_gitlab_project_members(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert result["results"] == [
        {
            "username": "jdoe",
            "avatar_url": "https://gitlab.example.com/avatar/jdoe",
            "name": "John Doe",
        }
    ]


@responses.activate
def test_post_comment_to_gitlab__issue__posts_note() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/issues/5/notes",
        json={"id": 100, "body": "test comment"},
        match=[header_matcher(EXPECTED_HEADERS)],
        status=201,
    )

    # When
    result = post_comment_to_gitlab(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
        resource_type="issues",
        resource_iid=5,
        body="test comment",
    )

    # Then
    assert result == {"id": 100, "body": "test comment"}


@responses.activate
def test_create_gitlab_issue__valid_data__creates_issue() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/issues",
        json={
            "iid": 42,
            "title": "Cleanup flag",
            "state": "opened",
            "web_url": f"{INSTANCE_URL}/group/project/-/issues/42",
        },
        match=[header_matcher(EXPECTED_HEADERS)],
        status=201,
    )

    # When
    result = create_gitlab_issue(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
        title="Cleanup flag",
        body="Remove stale flag",
    )

    # Then
    assert result["title"] == "Cleanup flag"
    assert result["iid"] == 42


@responses.activate
def test_get_gitlab_resource_metadata__valid_resource__returns_title_and_state() -> (
    None
):
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects/1/issues/5",
        json={"title": "Bug fix", "state": "opened", "extra_field": "ignored"},
        match=[header_matcher(EXPECTED_HEADERS)],
        status=200,
    )

    # When
    result = get_gitlab_resource_metadata(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
        resource_type="issues",
        resource_iid=5,
    )

    # Then
    assert result == {"title": "Bug fix", "state": "opened"}


@responses.activate
def test_create_flagsmith_flag_label__happy_path__creates_label() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/labels",
        json={"id": 10, "name": "Flagsmith Flag"},
        match=[header_matcher(EXPECTED_HEADERS)],
        status=201,
    )

    # When
    result = create_flagsmith_flag_label(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
    )

    # Then
    assert result == {"id": 10, "name": "Flagsmith Flag"}


@responses.activate
def test_create_flagsmith_flag_label__already_exists__returns_none() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/labels",
        json={"message": "Label already exists"},
        status=409,
    )

    # When
    result = create_flagsmith_flag_label(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
    )

    # Then
    assert result is None


@responses.activate
def test_create_flagsmith_flag_label__other_error__raises() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/labels",
        json={"message": "Forbidden"},
        status=403,
    )

    # When / Then
    with pytest.raises(HTTPError):
        create_flagsmith_flag_label(
            instance_url=INSTANCE_URL,
            access_token=ACCESS_TOKEN,
            gitlab_project_id=1,
        )


@responses.activate
def test_label_gitlab_resource__happy_path__adds_label() -> None:
    # Given
    responses.add(
        responses.PUT,
        f"{INSTANCE_URL}/api/v4/projects/1/issues/5",
        json={"id": 5, "labels": ["Flagsmith Flag"]},
        match=[header_matcher(EXPECTED_HEADERS)],
        status=200,
    )

    # When
    result = label_gitlab_resource(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
        resource_type="issues",
        resource_iid=5,
    )

    # Then
    assert result["labels"] == ["Flagsmith Flag"]


@pytest.mark.parametrize(
    "x_page,x_total_pages,expect_previous,expect_next",
    [
        ("2", "3", 1, 3),
        ("1", "3", None, 2),
        ("3", "3", 2, None),
        ("1", "1", None, None),
    ],
    ids=["middle-page", "first-page", "last-page", "single-page"],
)
def test_build_paginated_response__pagination_headers__returns_correct_links(
    x_page: str,
    x_total_pages: str,
    expect_previous: int | None,
    expect_next: int | None,
) -> None:
    # Given
    resp = _requests.models.Response()
    resp.headers["x-page"] = x_page
    resp.headers["x-total-pages"] = x_total_pages

    # When
    results: list[GitLabProject] = [
        {"id": 1, "name": "p", "path_with_namespace": "g/p"}
    ]
    result = _build_paginated_response(
        results=results,
        response=resp,
        total_count=10,
    )

    # Then
    assert result.get("previous") == expect_previous
    assert result.get("next") == expect_next
    assert result["total_count"] == 10


@pytest.mark.parametrize(
    "page,page_size,expected_error",
    [
        (0, 100, "Page must be greater or equal than 1"),
        (-1, 100, "Page must be greater or equal than 1"),
        (1, 0, "Page size must be an integer between 1 and 100"),
        (1, 101, "Page size must be an integer between 1 and 100"),
    ],
    ids=["page-zero", "page-negative", "page-size-zero", "page-size-over-100"],
)
def test_paginated_query_params__invalid_values__raises_value_error(
    page: int,
    page_size: int,
    expected_error: str,
) -> None:
    # Given
    # When
    # Then
    with pytest.raises(ValueError, match=expected_error):
        PaginatedQueryParams(page=page, page_size=page_size)
