import pytest
import requests
import responses

from integrations.gitlab.client import (
    create_issue_note,
    create_merge_request_note,
    fetch_gitlab_projects,
    search_gitlab_issues,
    search_gitlab_merge_requests,
)

INSTANCE_URL = "https://gitlab.example.com"
ACCESS_TOKEN = "glpat-test-token"


@responses.activate
def test_fetch_gitlab_projects__single_page__returns_projects_and_page_metadata() -> (
    None
):
    # Given
    responses.get(
        f"{INSTANCE_URL}/api/v4/projects",
        json=[
            {
                "id": 1,
                "name": "My Project",
                "path_with_namespace": "group/my-project",
                "extra_field": "ignored",
            },
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
        match=[responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN})],
    )

    # When
    result = fetch_gitlab_projects(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        page=1,
        page_size=100,
    )

    # Then
    assert result["results"] == [
        {"id": 1, "name": "My Project", "path_with_namespace": "group/my-project"},
    ]
    assert result["current_page"] == 1
    assert result["total_pages"] == 1
    assert result["total_count"] == 1


@responses.activate
def test_fetch_gitlab_projects__second_page__returns_correct_page_metadata() -> None:
    # Given
    responses.get(
        f"{INSTANCE_URL}/api/v4/projects",
        json=[{"id": 2, "name": "P2", "path_with_namespace": "g/p2"}],
        headers={"x-page": "2", "x-total-pages": "3", "x-total": "250"},
        match=[responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN})],
    )

    # When
    result = fetch_gitlab_projects(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        page=2,
        page_size=100,
    )

    # Then
    assert result["current_page"] == 2
    assert result["total_pages"] == 3
    assert result["total_count"] == 250


@responses.activate
def test_search_gitlab_issues__default_params__returns_issues() -> None:
    # Given
    responses.get(
        f"{INSTANCE_URL}/api/v4/projects/42/issues",
        json=[
            {
                "web_url": "https://gitlab.example.com/g/p/-/issues/1",
                "id": 101,
                "title": "Bug report",
                "iid": 1,
                "state": "opened",
            },
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
        match=[responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN})],
    )

    # When
    result = search_gitlab_issues(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=42,
        page=1,
        page_size=100,
    )

    # Then
    assert result["results"] == [
        {
            "web_url": "https://gitlab.example.com/g/p/-/issues/1",
            "id": 101,
            "title": "Bug report",
            "iid": 1,
            "state": "opened",
        },
    ]


@responses.activate
def test_search_gitlab_issues__with_search_text__sends_search_param() -> None:
    # Given
    responses.get(
        f"{INSTANCE_URL}/api/v4/projects/42/issues",
        json=[],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "0"},
        match=[
            responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN}),
            responses.matchers.query_param_matcher(
                {"per_page": "100", "page": "1", "state": "opened", "search": "login"},
                strict_match=False,
            ),
        ],
    )

    # When
    result = search_gitlab_issues(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=42,
        page=1,
        page_size=100,
        search_text="login",
    )

    # Then
    assert result["results"] == []
    assert result["total_count"] == 0


@responses.activate
def test_search_gitlab_merge_requests__default_params__returns_merge_requests() -> None:
    # Given
    responses.get(
        f"{INSTANCE_URL}/api/v4/projects/42/merge_requests",
        json=[
            {
                "web_url": "https://gitlab.example.com/g/p/-/merge_requests/5",
                "id": 201,
                "title": "Add feature",
                "iid": 5,
                "state": "opened",
                "merged_at": None,
                "draft": False,
            },
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
        match=[responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN})],
    )

    # When
    result = search_gitlab_merge_requests(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=42,
        page=1,
        page_size=100,
    )

    # Then
    assert result["results"] == [
        {
            "web_url": "https://gitlab.example.com/g/p/-/merge_requests/5",
            "id": 201,
            "title": "Add feature",
            "iid": 5,
            "state": "opened",
            "merged": False,
            "draft": False,
        },
    ]


@responses.activate
def test_search_gitlab_merge_requests__merged_mr__merged_is_true() -> None:
    # Given
    responses.get(
        f"{INSTANCE_URL}/api/v4/projects/42/merge_requests",
        json=[
            {
                "web_url": "https://gitlab.example.com/g/p/-/merge_requests/6",
                "id": 202,
                "title": "Merged MR",
                "iid": 6,
                "state": "merged",
                "merged_at": "2026-01-01T00:00:00Z",
                "draft": False,
            },
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
        match=[
            responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN}),
            responses.matchers.query_param_matcher(
                {"per_page": "100", "page": "1", "state": "merged", "search": "deploy"},
                strict_match=False,
            ),
        ],
    )

    # When
    result = search_gitlab_merge_requests(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        gitlab_project_id=42,
        page=1,
        page_size=100,
        search_text="deploy",
        state="merged",
    )

    # Then
    assert result["results"][0]["merged"] is True


@responses.activate
def test_create_issue_note__valid_request__posts_to_notes_api() -> None:
    # Given
    responses.post(
        f"{INSTANCE_URL}/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
        status=201,
        match=[
            responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN}),
            responses.matchers.json_params_matcher({"body": "Test comment"}),
        ],
    )

    # When
    create_issue_note(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        project_path="testorg/testrepo",
        issue_iid=42,
        body="Test comment",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_create_issue_note__server_error__raises() -> None:
    # Given
    responses.post(
        f"{INSTANCE_URL}/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        status=500,
    )

    # When / Then
    with pytest.raises(requests.HTTPError):
        create_issue_note(
            instance_url=INSTANCE_URL,
            access_token=ACCESS_TOKEN,
            project_path="testorg/testrepo",
            issue_iid=42,
            body="Test comment",
        )


@responses.activate
def test_create_merge_request_note__valid_request__posts_to_notes_api() -> None:
    # Given
    responses.post(
        f"{INSTANCE_URL}/api/v4/projects/testorg%2Ftestrepo/merge_requests/7/notes",
        json={"id": 2},
        status=201,
        match=[
            responses.matchers.header_matcher({"PRIVATE-TOKEN": ACCESS_TOKEN}),
            responses.matchers.json_params_matcher({"body": "MR comment"}),
        ],
    )

    # When
    create_merge_request_note(
        instance_url=INSTANCE_URL,
        access_token=ACCESS_TOKEN,
        project_path="testorg/testrepo",
        merge_request_iid=7,
        body="MR comment",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_create_merge_request_note__server_error__raises() -> None:
    # Given
    responses.post(
        f"{INSTANCE_URL}/api/v4/projects/testorg%2Ftestrepo/merge_requests/7/notes",
        status=500,
    )

    # When / Then
    with pytest.raises(requests.HTTPError):
        create_merge_request_note(
            instance_url=INSTANCE_URL,
            access_token=ACCESS_TOKEN,
            project_path="testorg/testrepo",
            merge_request_iid=7,
            body="MR comment",
        )
