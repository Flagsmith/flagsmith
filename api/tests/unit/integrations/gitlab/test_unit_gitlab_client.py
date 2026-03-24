import json

import pytest
import responses

from integrations.gitlab.client import (
    build_paginated_response,
    build_request_headers,
    create_flagsmith_flag_label,
    create_gitlab_issue,
    fetch_gitlab_project_members,
    fetch_gitlab_projects,
    fetch_search_gitlab_resource,
    get_gitlab_issue_mr_title_and_state,
    label_gitlab_issue_mr,
    post_comment_to_gitlab,
)
from integrations.gitlab.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    ProjectQueryParams,
)

INSTANCE_URL = "https://gitlab.example.com"
ACCESS_TOKEN = "test-access-token"


def test_build_request_headers__valid_token__returns_correct_headers() -> None:
    # Given / When
    headers = build_request_headers(ACCESS_TOKEN)
    # Then
    assert headers == {"PRIVATE-TOKEN": ACCESS_TOKEN}


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
    assert result["results"][0]["id"] == 1
    assert result["results"][0]["path_with_namespace"] == "group/my-project"


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
        status=200,
        headers={"x-total": "1"},
    )
    params = IssueQueryParams(gitlab_project_id=1, project_name="group/project")

    # When
    result = fetch_search_gitlab_resource(
        resource_type="issue",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Bug fix"


@responses.activate
def test_post_comment_to_gitlab__issue__posts_note() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/issues/5/notes",
        json={"id": 100, "body": "test comment"},
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
    assert result["body"] == "test comment"


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


@responses.activate
def test_get_gitlab_issue_mr_title_and_state__valid_resource__returns_metadata() -> (
    None
):
    # Given
    responses.add(
        responses.GET,
        f"{INSTANCE_URL}/api/v4/projects/1/issues/5",
        json={"title": "Bug fix", "state": "opened"},
        status=200,
    )

    # When
    result = get_gitlab_issue_mr_title_and_state(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
        resource_type="issues",
        resource_iid=5,
    )

    # Then
    assert result == {"title": "Bug fix", "state": "opened"}


# ---------------------------------------------------------------
# fetch_gitlab_project_members tests
# ---------------------------------------------------------------


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
    assert len(result["results"]) == 1
    assert result["results"][0]["username"] == "jdoe"
    assert result["results"][0]["name"] == "John Doe"


# ---------------------------------------------------------------
# create_flagsmith_flag_label tests
# ---------------------------------------------------------------


@responses.activate
def test_create_flagsmith_flag_label__happy_path__creates_label() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/labels",
        json={"id": 10, "name": "Flagsmith Flag"},
        status=201,
    )

    # When
    result = create_flagsmith_flag_label(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
    )

    # Then
    assert result is not None
    assert result["name"] == "Flagsmith Flag"


@responses.activate
def test_create_flagsmith_flag_label__already_exists__returns_none() -> None:
    # Given
    responses.add(
        responses.POST,
        f"{INSTANCE_URL}/api/v4/projects/1/labels",
        body=json.dumps({"message": "Label already exists"}),
        status=409,
        content_type="application/json",
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
        body=json.dumps({"message": "Forbidden"}),
        status=403,
        content_type="application/json",
    )

    # When / Then
    with pytest.raises(Exception):
        create_flagsmith_flag_label(
            instance_url=INSTANCE_URL,
            access_token=ACCESS_TOKEN,
            gitlab_project_id=1,
        )


# ---------------------------------------------------------------
# label_gitlab_issue_mr tests
# ---------------------------------------------------------------


@responses.activate
def test_label_gitlab_issue_mr__happy_path__adds_label() -> None:
    # Given
    responses.add(
        responses.PUT,
        f"{INSTANCE_URL}/api/v4/projects/1/issues/5",
        json={"id": 5, "labels": ["Flagsmith Flag"]},
        status=200,
    )

    # When
    result = label_gitlab_issue_mr(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=1,
        resource_type="issues",
        resource_iid=5,
    )

    # Then
    assert result["labels"] == ["Flagsmith Flag"]


# ---------------------------------------------------------------
# build_paginated_response tests
# ---------------------------------------------------------------


def test_build_paginated_response__pagination_headers__returns_previous_and_next() -> (
    None
):
    # Given
    import requests

    resp = requests.models.Response()
    resp.headers["x-page"] = "2"
    resp.headers["x-total-pages"] = "3"

    # When
    result = build_paginated_response(
        results=[{"id": 1}],
        response=resp,
        total_count=10,
    )

    # Then
    assert result["previous"] == 1
    assert result["next"] == 3
    assert result["total_count"] == 10


def test_build_paginated_response__first_page__no_previous() -> None:
    # Given
    import requests

    resp = requests.models.Response()
    resp.headers["x-page"] = "1"
    resp.headers["x-total-pages"] = "3"

    # When
    result = build_paginated_response(
        results=[{"id": 1}],
        response=resp,
    )

    # Then
    assert "previous" not in result
    assert result["next"] == 2


def test_build_paginated_response__last_page__no_next() -> None:
    # Given
    import requests

    resp = requests.models.Response()
    resp.headers["x-page"] = "3"
    resp.headers["x-total-pages"] = "3"

    # When
    result = build_paginated_response(
        results=[{"id": 1}],
        response=resp,
    )

    # Then
    assert result["previous"] == 2
    assert "next" not in result


# ---------------------------------------------------------------
# fetch_search_gitlab_resource — optional filter params
# ---------------------------------------------------------------


@responses.activate
def test_fetch_search_gitlab_resource__with_search_text__appends_search_param() -> None:
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
        search_text="my search",
    )

    # When
    fetch_search_gitlab_resource(
        resource_type="issue",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert len(responses.calls) == 1
    request_url: str = responses.calls[0].request.url  # type: ignore[union-attr]
    assert "search=my+search" in request_url or "search=my%20search" in request_url


@responses.activate
def test_fetch_search_gitlab_resource__with_author__appends_author_param() -> None:
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
        author="jdoe",
    )

    # When
    fetch_search_gitlab_resource(
        resource_type="issue",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert len(responses.calls) == 1
    request_url: str = responses.calls[0].request.url  # type: ignore[union-attr]
    assert "author_username=jdoe" in request_url


@responses.activate
def test_fetch_search_gitlab_resource__with_assignee__appends_assignee_param() -> None:
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
        assignee="jsmith",
    )

    # When
    fetch_search_gitlab_resource(
        resource_type="issue",
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        params=params,
    )

    # Then
    assert len(responses.calls) == 1
    request_url: str = responses.calls[0].request.url  # type: ignore[union-attr]
    assert "assignee_username=jsmith" in request_url
