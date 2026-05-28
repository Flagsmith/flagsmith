# Azure DevOps Integration — PR 5: Browse endpoints

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the ADO REST client with `list_repositories`, `list_pull_requests`, and `list_work_items`, then expose four paginated browse endpoints (`projects`, `repositories`, `pull-requests`, `work-items`) under `/api/v1/projects/{flagsmith_project_id}/azure-devops/`. After this PR, the future frontend picker can typeahead-search ADO content via Flagsmith's API.

**Architecture:** Mirror the GitLab browse-views layout exactly — a shared `_AdoListView` base with permission/auth handling, four concrete subclasses, query-param serializers, and one client function per resource type. The work-item endpoint is the only non-trivial piece: ADO has no direct text-search endpoint for work items, so we issue a `POST /_apis/wit/wiql` (returns IDs) followed by a `POST /_apis/wit/workitemsbatch` (hydrates the matched IDs into full work-item rows). PR search by title is **not supported** by ADO's REST API — PR browse exposes only state filtering. Pagination uses ADO's native continuation-token model; the response wraps the token as a `next` URL.

**Tech Stack:** Python 3.12, Django 5.x, DRF, `requests`, `responses` (tests), pytest, mypy strict.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Components → `views/browse_azure_devops.py`", "Components → `client/api.py`", "Components → `mappers.py`", "Data flow → Browse flow", "Work-item search internals".

**Plan reference (parent):** `docs/superpowers/plans/2026-05-28-azure-devops-04-tagging.md`.

**Stack position:** PR 5 of N. Branches off `feat/azure-devops-04-tagging`. Branch name: `feat/azure-devops-05-browse`.

---

## Spec deviations / clarifications captured here

1. **PR title search is not supported.** ADO's `GET /_apis/git/pullrequests` only exposes `searchCriteria.status` + a handful of reviewer/creator filters — no text search. The spec implied text search worked for both PRs and work items; in practice it only works for work items (via WIQL `CONTAINS`). PR browse exposes `?state=` only.
2. **`workitemsbatch` is `POST`, not `GET`.** The spec said `GET workitemsbatch`; ADO's REST docs (any version) require `POST` with the IDs in the body. Implementing as `POST`.
3. **Browse URL prefix is `/{project_pk}/azure-devops/...`, not `/{project_pk}/integrations/azure-devops/...`** to avoid routing conflict with the CRUD viewset's `{pk}` capture. Matches GitLab's precedent (`/{project_pk}/gitlab/projects/` etc.).
4. **Pagination shape differs from GitLab.** GitLab returns `{count, next, previous, results}` with offset paging. ADO uses continuation tokens; this PR returns `{results, next, previous}` where `next` is a URL containing `continuation_token=<token>` and `previous` is always `null` (ADO continuation tokens don't reverse-paginate). `count` is omitted — ADO doesn't return totals.

---

## Scope deliberately out of PR 5

- ADO Code Search API (separate service, separate auth) — would enable PR title search, but is too much surface for v1.
- Work-item type discovery (`/_apis/wit/workitemtypes`) — the frontend hardcodes common types or accepts free text in v1.
- Frontend picker components — separate PR.
- ADO request-duration metric — lands with the rest of `metrics.py` later.

---

## File Structure

- **Modify:** `api/integrations/azure_devops/client/types.py` — add `AdoRepository`, `AdoPullRequest`, `AdoPullRequestsPage`, `AdoWorkItem`, `AdoWorkItemsPage` TypedDicts.
- **Modify:** `api/integrations/azure_devops/client/api.py` — add `list_repositories`, `list_pull_requests`, `list_work_items` (the last orchestrates `_wiql_query_for_work_items` + `_get_workitems_batch`).
- **Modify:** `api/integrations/azure_devops/client/__init__.py` — re-export the new public surface.
- **Create:** `api/integrations/azure_devops/serializers/browse.py` — `AdoBrowseQueryParamsSerializer` (page-size + continuation token), plus three resource-specific subclasses (repositories, pull-requests, work-items). Lives in a new `serializers/` subpackage so `serializers.py` (PR 2's configuration serializer) doesn't grow into a kitchen sink.
- **Modify:** `api/integrations/azure_devops/serializers.py` → rename to `api/integrations/azure_devops/serializers/__init__.py` to keep the configuration serializer importable at the same path. (Python sees `serializers/__init__.py` as the package `serializers`; existing `from integrations.azure_devops.serializers import AzureDevOpsConfigurationSerializer` imports keep working.)
- **Create:** `api/integrations/azure_devops/views/browse_azure_devops.py` — `_AdoListView` base + four concrete views (`BrowseAdoProjects`, `BrowseAdoRepositories`, `BrowseAdoPullRequests`, `BrowseAdoWorkItems`).
- **Modify:** `api/integrations/azure_devops/views/__init__.py` — re-export the four browse views.
- **Modify:** `api/projects/urls.py` — add four `path()` entries for the browse views.
- **Modify:** `api/integrations/azure_devops/mappers.py` — extend with `map_ado_pr_response_to_page`, `map_ado_work_items_response_to_page` (the JSON → TypedDict transformations).
- **Modify:** `api/tests/unit/integrations/azure_devops/test_client.py` — append tests for the three new client functions.
- **Create:** `api/tests/unit/integrations/azure_devops/test_browse_views.py` — integration tests for each browse view.

The serializer-subpackage split is a small structural change. The PR 2 configuration serializer (`AzureDevOpsConfigurationSerializer`, `WRITE_ONLY_PLACEHOLDER`) moves verbatim into `serializers/__init__.py` so all existing imports of `integrations.azure_devops.serializers` keep working. New browse query-param serializers live in `serializers/browse.py`.

---

## Pre-flight

- [ ] **Step 0: Confirm working branch**

```bash
cd /Users/asaphkotzin/Dev/flagsmith
git status
git log --oneline -3
```

Expected: branch `feat/azure-devops-05-browse`, HEAD at PR 4's tip (`6193e5ef5`). Working tree clean. If not, create the branch off `feat/azure-devops-04-tagging`:

```bash
git checkout feat/azure-devops-04-tagging
git checkout -b feat/azure-devops-05-browse
```

---

## Task 1: TypedDicts for new resource types

**Files:**
- Modify: `api/integrations/azure_devops/client/types.py`

- [ ] **Step 1: Write the smoke tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
from integrations.azure_devops.client.types import (
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
    AdoWorkItem,
    AdoWorkItemsPage,
)


def test_ado_repository__shape__has_required_keys() -> None:
    # Given
    repo: AdoRepository = {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "my-repo",
        "default_branch": "refs/heads/main",
    }

    # When
    keys = set(repo.keys())

    # Then
    assert keys == {"id", "name", "default_branch"}


def test_ado_pull_request__shape__has_required_keys() -> None:
    # Given
    pr: AdoPullRequest = {
        "id": 42,
        "title": "Add feature X",
        "state": "active",
        "is_draft": False,
        "web_url": "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42",
        "repository_name": "repo",
    }

    # When
    keys = set(pr.keys())

    # Then
    assert keys == {"id", "title", "state", "is_draft", "web_url", "repository_name"}


def test_ado_pull_requests_page__shape__has_required_keys() -> None:
    # Given
    page: AdoPullRequestsPage = {"results": [], "continuation_token": None}

    # When
    keys = set(page.keys())

    # Then
    assert keys == {"results", "continuation_token"}


def test_ado_work_item__shape__has_required_keys() -> None:
    # Given
    work_item: AdoWorkItem = {
        "id": 100,
        "title": "Fix bug",
        "state": "Active",
        "work_item_type": "Bug",
        "web_url": "https://dev.azure.com/test-org/proj/_workitems/edit/100",
    }

    # When
    keys = set(work_item.keys())

    # Then
    assert keys == {"id", "title", "state", "work_item_type", "web_url"}


def test_ado_work_items_page__shape__has_required_keys() -> None:
    # Given
    page: AdoWorkItemsPage = {"results": [], "continuation_token": None}

    # When
    keys = set(page.keys())

    # Then
    assert keys == {"results", "continuation_token"}
```

- [ ] **Step 2: Run to verify failure**

From `api/`:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
```

Expected: collection errors — five TypedDicts not importable.

- [ ] **Step 3: Extend `client/types.py`**

The current `api/integrations/azure_devops/client/types.py` is:

```python
from typing import TypedDict


class AdoProject(TypedDict):
    id: str
    name: str
    url: str


class AdoProjectsPage(TypedDict):
    results: list[AdoProject]
    continuation_token: str | None
```

Replace with:

```python
from typing import TypedDict


class AdoProject(TypedDict):
    id: str
    name: str
    url: str


class AdoProjectsPage(TypedDict):
    results: list[AdoProject]
    continuation_token: str | None


class AdoRepository(TypedDict):
    id: str
    name: str
    default_branch: str


class AdoPullRequest(TypedDict):
    id: int
    title: str
    state: str
    is_draft: bool
    web_url: str
    repository_name: str


class AdoPullRequestsPage(TypedDict):
    results: list[AdoPullRequest]
    continuation_token: str | None


class AdoWorkItem(TypedDict):
    id: int
    title: str
    state: str
    work_item_type: str
    web_url: str


class AdoWorkItemsPage(TypedDict):
    results: list[AdoWorkItem]
    continuation_token: str | None
```

- [ ] **Step 4: Run tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
```

Expected: all client tests pass (PR 3 baseline + 5 new shape tests).

- [ ] **Step 5: mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/client/types.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add TypedDicts for Azure DevOps browse responses

Five new types covering the resource shapes the browse endpoints will
return: AdoRepository, AdoPullRequest, AdoPullRequestsPage, AdoWorkItem,
AdoWorkItemsPage. Same page-shape (results + continuation_token) as
AdoProjectsPage — ADO's REST API uses continuation tokens uniformly.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `list_repositories` client function

**Files:**
- Modify: `api/integrations/azure_devops/client/api.py`
- Modify: `api/integrations/azure_devops/client/__init__.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py`

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
@responses.activate
def test_list_repositories__valid_response__returns_typed_list() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/repositories",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000bb1",
                    "name": "frontend",
                    "defaultBranch": "refs/heads/main",
                    "extra": "ignored",
                },
                {
                    "id": "00000000-0000-0000-0000-000000000bb2",
                    "name": "backend",
                    "defaultBranch": "refs/heads/develop",
                },
            ],
            "count": 2,
        },
    )

    # When
    repos = list_repositories(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then
    assert repos == [
        {
            "id": "00000000-0000-0000-0000-000000000bb1",
            "name": "frontend",
            "default_branch": "refs/heads/main",
        },
        {
            "id": "00000000-0000-0000-0000-000000000bb2",
            "name": "backend",
            "default_branch": "refs/heads/develop",
        },
    ]


@responses.activate
def test_list_repositories__missing_default_branch__defaults_to_empty_string() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-000000000aa1"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/repositories",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000bb3",
                    "name": "empty-repo",
                },
            ],
            "count": 1,
        },
    )

    # When
    repos = list_repositories(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then — ADO omits `defaultBranch` for repos with no commits yet
    assert repos[0]["default_branch"] == ""
```

The `list_repositories` import will be added in Step 4.

- [ ] **Step 2: Run tests to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py::test_list_repositories__valid_response__returns_typed_list -v'
```

Expected: import error.

- [ ] **Step 3: Add `list_repositories` to `api/integrations/azure_devops/client/api.py`**

Append the following function to the existing file:

```python
def list_repositories(
    *,
    organisation_url: str,
    pat: str,
    ado_project_id: str,
) -> list[AdoRepository]:
    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path=f"{ado_project_id}/_apis/git/repositories",
    )
    payload = response.json()
    return [
        AdoRepository(
            id=item["id"],
            name=item["name"],
            default_branch=item.get("defaultBranch", ""),
        )
        for item in payload.get("value", [])
    ]
```

Add `AdoRepository` to the imports at the top of the file:

```python
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoRepository,
)
```

Note: the `_ado_request` helper from PR 3 prefixes `/_apis/` automatically. For project-scoped paths like `{ado_project_id}/_apis/git/repositories`, we need the prefix to be different. Update `_ado_request` to accept paths that already contain `_apis/`:

Find the current `_ado_request` body:

```python
def _ado_request(
    method: str,
    organisation_url: str,
    pat: str,
    *,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    base = organisation_url.rstrip("/")
    query: dict[str, Any] = {"api-version": AZURE_DEVOPS_API_VERSION}
    if params:
        query.update(params)
    response = requests.request(
        method,
        f"{base}/_apis/{path}",
        ...
```

Replace the URL composition with:

```python
def _ado_request(
    method: str,
    organisation_url: str,
    pat: str,
    *,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    base = organisation_url.rstrip("/")
    # `path` may be either a bare segment ("projects") or already contain
    # "_apis/" (for project-scoped endpoints like "{ado_project_id}/_apis/git/...").
    # If it already mentions "_apis/", treat it as a complete suffix.
    if "_apis/" in path:
        url = f"{base}/{path}"
    else:
        url = f"{base}/_apis/{path}"
    query: dict[str, Any] = {"api-version": AZURE_DEVOPS_API_VERSION}
    if params:
        query.update(params)
    response = requests.request(
        method,
        url,
        ...
```

Keep the rest of `_ado_request` unchanged.

Verify the PR 3 test `test_list_projects__trailing_slash_in_org_url__normalised_in_request` still passes — `list_projects` calls with `path="projects"` (no `_apis/`), so it takes the second branch and produces `{base}/_apis/projects` as before.

- [ ] **Step 4: Re-export from `client/__init__.py`**

Update `api/integrations/azure_devops/client/__init__.py` to add `list_repositories` and `AdoRepository` to the exports. The final file:

```python
from integrations.azure_devops.client.api import (
    list_projects,
    list_repositories,
)
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoRepository,
)

__all__ = [
    "AdoProject",
    "AdoProjectsPage",
    "AdoRepository",
    "AzureDevOpsAuthError",
    "AzureDevOpsError",
    "AzureDevOpsNotFoundError",
    "list_projects",
    "list_repositories",
]
```

Then update the imports in the new tests to actually import `list_repositories`:

In `api/tests/unit/integrations/azure_devops/test_client.py`, find the existing import block and extend it to:

```python
from integrations.azure_devops.client import (
    list_projects,
    list_repositories,
)
```

- [ ] **Step 5: Run tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
```

Expected: all client tests pass.

- [ ] **Step 6: mypy + lint**

```bash
make typecheck && make lint
```

Expected: both clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/client/api.py api/integrations/azure_devops/client/__init__.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add list_repositories to the Azure DevOps client

Lists git repositories within an ADO project. Generalises _ado_request
to accept paths that already contain "_apis/" (project-scoped
endpoints) alongside the existing bare-path shape. defaultBranch is
optional on the wire (ADO omits it for empty repos) so we default to
"" when absent.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `list_pull_requests` client function

**Files:**
- Modify: `api/integrations/azure_devops/client/api.py`
- Modify: `api/integrations/azure_devops/client/__init__.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py`

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
@responses.activate
def test_list_pull_requests__default_params__filters_state_active() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/pullrequests",
        json={
            "value": [
                {
                    "pullRequestId": 42,
                    "title": "Add feature X",
                    "status": "active",
                    "isDraft": False,
                    "repository": {"name": "frontend"},
                    "_links": {
                        "web": {
                            "href": "https://dev.azure.com/test-org/proj/_git/frontend/pullrequest/42"
                        }
                    },
                },
            ],
            "count": 1,
        },
        match=[
            responses.matchers.query_param_matcher(
                {"searchCriteria.status": "active"},
                strict_match=False,
            )
        ],
    )

    # When
    page = list_pull_requests(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then
    assert page["results"] == [
        {
            "id": 42,
            "title": "Add feature X",
            "state": "active",
            "is_draft": False,
            "web_url": "https://dev.azure.com/test-org/proj/_git/frontend/pullrequest/42",
            "repository_name": "frontend",
        },
    ]
    assert page["continuation_token"] is None


@responses.activate
def test_list_pull_requests__state_completed__sends_completed_in_query() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/pullrequests",
        json={"value": [], "count": 0},
        match=[
            responses.matchers.query_param_matcher(
                {"searchCriteria.status": "completed"},
                strict_match=False,
            )
        ],
    )

    # When
    list_pull_requests(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        state="completed",
    )

    # Then — matched URL implies the right query
    assert len(responses.calls) == 1


@responses.activate
def test_list_pull_requests__continuation_token_in_header__exposed_on_page() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/pullrequests",
        json={"value": [], "count": 0},
        headers={"x-ms-continuationtoken": "pr-next"},
    )

    # When
    page = list_pull_requests(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then
    assert page["continuation_token"] == "pr-next"
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py::test_list_pull_requests__default_params__filters_state_active -v'
```

Expected: import error.

- [ ] **Step 3: Add `list_pull_requests` to `api/integrations/azure_devops/client/api.py`**

Append:

```python
def list_pull_requests(
    *,
    organisation_url: str,
    pat: str,
    ado_project_id: str,
    state: str = "active",
    top: int | None = None,
    continuation_token: str | None = None,
) -> AdoPullRequestsPage:
    params: dict[str, Any] = {"searchCriteria.status": state}
    if top is not None:
        params["$top"] = top
    if continuation_token is not None:
        params["continuationToken"] = continuation_token

    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path=f"{ado_project_id}/_apis/git/pullrequests",
        params=params,
    )
    payload = response.json()
    results: list[AdoPullRequest] = [
        AdoPullRequest(
            id=item["pullRequestId"],
            title=item["title"],
            state=item["status"],
            is_draft=item.get("isDraft", False),
            web_url=item.get("_links", {}).get("web", {}).get("href", ""),
            repository_name=item.get("repository", {}).get("name", ""),
        )
        for item in payload.get("value", [])
    ]
    next_token = response.headers.get("x-ms-continuationtoken")
    return AdoPullRequestsPage(results=results, continuation_token=next_token)
```

Update the imports at the top of `api/integrations/azure_devops/client/api.py`:

```python
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
)
```

- [ ] **Step 4: Re-export from `client/__init__.py`**

The final file:

```python
from integrations.azure_devops.client.api import (
    list_projects,
    list_pull_requests,
    list_repositories,
)
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
)

__all__ = [
    "AdoProject",
    "AdoProjectsPage",
    "AdoPullRequest",
    "AdoPullRequestsPage",
    "AdoRepository",
    "AzureDevOpsAuthError",
    "AzureDevOpsError",
    "AzureDevOpsNotFoundError",
    "list_projects",
    "list_pull_requests",
    "list_repositories",
]
```

Extend the test file's import block to include `list_pull_requests`.

- [ ] **Step 5: Run tests, mypy, lint, commit**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
make typecheck
make lint
```

Expected: all clean.

```bash
git add api/integrations/azure_devops/client/api.py api/integrations/azure_devops/client/__init__.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add list_pull_requests to the Azure DevOps client

Lists pull requests in an ADO project, filterable by state (active /
completed / abandoned / all). ADO's REST API doesn't expose a text
search for PRs, so this function takes state + paging only — title
search is a work-item-only capability.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `list_work_items` client function (WIQL + workitemsbatch)

**Files:**
- Modify: `api/integrations/azure_devops/client/api.py`
- Modify: `api/integrations/azure_devops/client/__init__.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py`

This is the most substantial function in PR 5. It orchestrates two ADO API calls:

1. `POST {org}/{ado_project_id}/_apis/wit/wiql` with body `{"query": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project AND ..."}` — returns just the matched IDs.
2. `POST {org}/_apis/wit/workitemsbatch` with body `{"ids": [...], "fields": ["System.Id", "System.Title", "System.State", "System.WorkItemType"]}` — hydrates the IDs with the fields we need.

Pagination is handled by slicing the WIQL result IDs (max 200 per WIQL response per ADO docs).

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
@responses.activate
def test_list_work_items__title_search_and_type__sends_wiql_and_hydrates() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    expected_wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.TeamProject] = @project "
        "AND [System.State] = 'Active' "
        "AND [System.WorkItemType] = 'Bug' "
        "AND [System.Title] CONTAINS 'login' "
        "ORDER BY [System.ChangedDate] DESC"
    )
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={
            "workItems": [{"id": 101}, {"id": 102}],
        },
        match=[
            responses.matchers.json_params_matcher({"query": expected_wiql_query}),
        ],
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 101,
                    "fields": {
                        "System.Title": "Login broken",
                        "System.State": "Active",
                        "System.WorkItemType": "Bug",
                    },
                    "_links": {
                        "html": {
                            "href": "https://dev.azure.com/test-org/proj/_workitems/edit/101"
                        }
                    },
                },
                {
                    "id": 102,
                    "fields": {
                        "System.Title": "Login slow",
                        "System.State": "Active",
                        "System.WorkItemType": "Bug",
                    },
                    "_links": {
                        "html": {
                            "href": "https://dev.azure.com/test-org/proj/_workitems/edit/102"
                        }
                    },
                },
            ]
        },
        match=[
            responses.matchers.json_params_matcher(
                {
                    "ids": [101, 102],
                    "fields": [
                        "System.Id",
                        "System.Title",
                        "System.State",
                        "System.WorkItemType",
                    ],
                }
            ),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        search_text="login",
        state="Active",
        work_item_type="Bug",
    )

    # Then
    assert page["results"] == [
        {
            "id": 101,
            "title": "Login broken",
            "state": "Active",
            "work_item_type": "Bug",
            "web_url": "https://dev.azure.com/test-org/proj/_workitems/edit/101",
        },
        {
            "id": 102,
            "title": "Login slow",
            "state": "Active",
            "work_item_type": "Bug",
            "web_url": "https://dev.azure.com/test-org/proj/_workitems/edit/102",
        },
    ]
    assert page["continuation_token"] is None


@responses.activate
def test_list_work_items__no_filters__produces_minimal_wiql() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    expected_wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.TeamProject] = @project "
        "ORDER BY [System.ChangedDate] DESC"
    )
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={"workItems": []},
        match=[
            responses.matchers.json_params_matcher({"query": expected_wiql_query}),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then — empty WIQL means no second call
    assert page["results"] == []
    assert len(responses.calls) == 1


@responses.activate
def test_list_work_items__search_text_with_quote__is_escaped() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    expected_wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.TeamProject] = @project "
        "AND [System.Title] CONTAINS 'O''Brien' "
        "ORDER BY [System.ChangedDate] DESC"
    )
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={"workItems": []},
        match=[
            responses.matchers.json_params_matcher({"query": expected_wiql_query}),
        ],
    )

    # When
    list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        search_text="O'Brien",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_list_work_items__pagination__slices_wiql_ids_by_top_and_returns_continuation() -> None:
    # Given — WIQL returns 5 IDs; we ask for top=2
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={
            "workItems": [
                {"id": 200},
                {"id": 201},
                {"id": 202},
                {"id": 203},
                {"id": 204},
            ]
        },
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 200,
                    "fields": {
                        "System.Title": "WI 200",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-200"}},
                },
                {
                    "id": 201,
                    "fields": {
                        "System.Title": "WI 201",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-201"}},
                },
            ]
        },
        match=[
            responses.matchers.json_params_matcher(
                {
                    "ids": [200, 201],
                    "fields": [
                        "System.Id",
                        "System.Title",
                        "System.State",
                        "System.WorkItemType",
                    ],
                }
            ),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        top=2,
    )

    # Then — first two IDs hydrated; continuation_token reflects offset of next batch
    assert [r["id"] for r in page["results"]] == [200, 201]
    assert page["continuation_token"] == "2"


@responses.activate
def test_list_work_items__continuation_token__starts_from_offset() -> None:
    # Given — same WIQL set, paginating with continuation_token="2"
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={
            "workItems": [
                {"id": 200},
                {"id": 201},
                {"id": 202},
                {"id": 203},
                {"id": 204},
            ]
        },
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 202,
                    "fields": {
                        "System.Title": "WI 202",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-202"}},
                },
                {
                    "id": 203,
                    "fields": {
                        "System.Title": "WI 203",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-203"}},
                },
            ]
        },
        match=[
            responses.matchers.json_params_matcher(
                {
                    "ids": [202, 203],
                    "fields": [
                        "System.Id",
                        "System.Title",
                        "System.State",
                        "System.WorkItemType",
                    ],
                }
            ),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        top=2,
        continuation_token="2",
    )

    # Then
    assert [r["id"] for r in page["results"]] == [202, 203]
    assert page["continuation_token"] == "4"


@responses.activate
def test_list_work_items__last_page__omits_continuation_token() -> None:
    # Given — only one item left; second batch returns it; no further pages
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={"workItems": [{"id": 999}]},
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 999,
                    "fields": {
                        "System.Title": "Final",
                        "System.State": "Closed",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-999"}},
                },
            ]
        },
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        top=10,
    )

    # Then — single result, no more pages
    assert page["results"][0]["id"] == 999
    assert page["continuation_token"] is None
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -k list_work_items -v'
```

Expected: import errors.

- [ ] **Step 3: Add `list_work_items` to `client/api.py`**

Append the following helper + public function:

```python
_WORK_ITEM_FIELDS = [
    "System.Id",
    "System.Title",
    "System.State",
    "System.WorkItemType",
]


def _wiql_query_for_work_items(
    *,
    search_text: str | None,
    state: str | None,
    work_item_type: str | None,
) -> str:
    clauses = ["[System.TeamProject] = @project"]
    if state:
        clauses.append(f"[System.State] = '{_escape_wiql_string(state)}'")
    if work_item_type:
        clauses.append(
            f"[System.WorkItemType] = '{_escape_wiql_string(work_item_type)}'"
        )
    if search_text:
        clauses.append(f"[System.Title] CONTAINS '{_escape_wiql_string(search_text)}'")
    where = " AND ".join(clauses)
    return (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE {where} "
        "ORDER BY [System.ChangedDate] DESC"
    )


def _escape_wiql_string(value: str) -> str:
    # WIQL escapes single quotes by doubling them. There is no other
    # escape character. We control the column names; only user-supplied
    # values need this.
    return value.replace("'", "''")


def list_work_items(
    *,
    organisation_url: str,
    pat: str,
    ado_project_id: str,
    search_text: str | None = None,
    state: str | None = None,
    work_item_type: str | None = None,
    top: int = 100,
    continuation_token: str | None = None,
) -> AdoWorkItemsPage:
    """List ADO work items in a project, filterable by title text, state,
    and work-item type. Implemented as a WIQL query for the IDs followed
    by a batch fetch for the rows we want to display.

    Pagination is offset-based on the WIQL ID list (ADO returns up to
    20,000 IDs in one WIQL response per the docs). ``continuation_token``
    encodes the offset into the WIQL ID list as a string integer; the
    response's ``continuation_token`` is the offset to ask for next, or
    ``None`` if no further pages remain.
    """
    query = _wiql_query_for_work_items(
        search_text=search_text,
        state=state,
        work_item_type=work_item_type,
    )
    wiql_response = _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{ado_project_id}/_apis/wit/wiql",
        json_body={"query": query},
    )
    wiql_payload = wiql_response.json()
    all_ids: list[int] = [item["id"] for item in wiql_payload.get("workItems", [])]
    if not all_ids:
        return AdoWorkItemsPage(results=[], continuation_token=None)

    offset = int(continuation_token) if continuation_token is not None else 0
    end = offset + top
    page_ids = all_ids[offset:end]
    if not page_ids:
        return AdoWorkItemsPage(results=[], continuation_token=None)

    batch_response = _ado_request(
        "POST",
        organisation_url,
        pat,
        path="wit/workitemsbatch",
        json_body={"ids": page_ids, "fields": _WORK_ITEM_FIELDS},
    )
    batch_payload = batch_response.json()
    results: list[AdoWorkItem] = [
        AdoWorkItem(
            id=item["id"],
            title=item.get("fields", {}).get("System.Title", ""),
            state=item.get("fields", {}).get("System.State", ""),
            work_item_type=item.get("fields", {}).get("System.WorkItemType", ""),
            web_url=item.get("_links", {}).get("html", {}).get("href", ""),
        )
        for item in batch_payload.get("value", [])
    ]
    next_token = str(end) if end < len(all_ids) else None
    return AdoWorkItemsPage(results=results, continuation_token=next_token)
```

Update the imports at the top of `client/api.py` to include `AdoWorkItem` and `AdoWorkItemsPage`:

```python
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
    AdoWorkItem,
    AdoWorkItemsPage,
)
```

- [ ] **Step 4: Re-export from `client/__init__.py`**

Final contents:

```python
from integrations.azure_devops.client.api import (
    list_projects,
    list_pull_requests,
    list_repositories,
    list_work_items,
)
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
    AdoWorkItem,
    AdoWorkItemsPage,
)

__all__ = [
    "AdoProject",
    "AdoProjectsPage",
    "AdoPullRequest",
    "AdoPullRequestsPage",
    "AdoRepository",
    "AdoWorkItem",
    "AdoWorkItemsPage",
    "AzureDevOpsAuthError",
    "AzureDevOpsError",
    "AzureDevOpsNotFoundError",
    "list_projects",
    "list_pull_requests",
    "list_repositories",
    "list_work_items",
]
```

Extend test imports to include `list_work_items`.

- [ ] **Step 5: Run tests, mypy, lint, commit**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
make typecheck
make lint
```

Expected: all clean.

```bash
git add api/integrations/azure_devops/client/api.py api/integrations/azure_devops/client/__init__.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add list_work_items to the Azure DevOps client

Implements work-item search via WIQL + workitemsbatch:
  1. POST /{project}/_apis/wit/wiql with a parameterised query for
     state, type, and title CONTAINS — returns matched IDs.
  2. POST /_apis/wit/workitemsbatch with the page-sized slice of IDs
     — returns rows with id/title/state/type/url.

Pagination is offset-based on the WIQL ID list (continuation_token is
the next offset as a stringified integer; None on the final page).
Single-quote escaping in CONTAINS uses WIQL's double-quote convention.
Column names are hard-coded; only user-supplied values are escaped.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Split serializers into a subpackage; add browse query-param serializers

**Files:**
- Move: `api/integrations/azure_devops/serializers.py` → `api/integrations/azure_devops/serializers/__init__.py`
- Create: `api/integrations/azure_devops/serializers/browse.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_serializers.py` — append browse-serializer tests; existing PR 2 tests continue to work unchanged.

- [ ] **Step 1: Move existing serializers to package init**

```bash
mkdir -p api/integrations/azure_devops/serializers
git mv api/integrations/azure_devops/serializers.py api/integrations/azure_devops/serializers/__init__.py
```

Verify existing imports still work:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py tests/unit/integrations/azure_devops/test_configuration.py -v'
```

Expected: all pass — the move is transparent to importers because `from integrations.azure_devops.serializers import X` resolves to `serializers/__init__.py`.

- [ ] **Step 2: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_serializers.py`:

```python
from integrations.azure_devops.serializers.browse import (
    AdoBrowseQueryParamsSerializer,
    AdoPullRequestsQueryParamsSerializer,
    AdoRepositoriesQueryParamsSerializer,
    AdoWorkItemsQueryParamsSerializer,
)


def test_browse_serializer__defaults__top_100_no_token() -> None:
    # Given
    serializer = AdoBrowseQueryParamsSerializer(data={})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data == {"top": 100}


def test_browse_serializer__valid_top_and_token__validates() -> None:
    # Given
    serializer = AdoBrowseQueryParamsSerializer(
        data={"top": 50, "continuation_token": "abc"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data == {"top": 50, "continuation_token": "abc"}


def test_browse_serializer__top_too_large__invalidates() -> None:
    # Given
    serializer = AdoBrowseQueryParamsSerializer(data={"top": 1000})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "top" in serializer.errors


def test_repositories_serializer__requires_ado_project_id() -> None:
    # Given
    serializer = AdoRepositoriesQueryParamsSerializer(data={})

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "ado_project_id" in serializer.errors


def test_pull_requests_serializer__state_default__is_active() -> None:
    # Given
    serializer = AdoPullRequestsQueryParamsSerializer(
        data={"ado_project_id": "00000000-0000-0000-0000-0000000000aa"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data["state"] == "active"


def test_pull_requests_serializer__invalid_state__rejected() -> None:
    # Given
    serializer = AdoPullRequestsQueryParamsSerializer(
        data={
            "ado_project_id": "00000000-0000-0000-0000-0000000000aa",
            "state": "weird",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert not is_valid
    assert "state" in serializer.errors


def test_work_items_serializer__all_fields_optional_except_project__validates() -> None:
    # Given
    serializer = AdoWorkItemsQueryParamsSerializer(
        data={"ado_project_id": "00000000-0000-0000-0000-0000000000aa"}
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data["ado_project_id"] == (
        "00000000-0000-0000-0000-0000000000aa"
    )


def test_work_items_serializer__with_filters__validates() -> None:
    # Given
    serializer = AdoWorkItemsQueryParamsSerializer(
        data={
            "ado_project_id": "00000000-0000-0000-0000-0000000000aa",
            "search_text": "login",
            "state": "Active",
            "work_item_type": "Bug",
        }
    )

    # When
    is_valid = serializer.is_valid()

    # Then
    assert is_valid
    assert serializer.validated_data["search_text"] == "login"
    assert serializer.validated_data["state"] == "Active"
    assert serializer.validated_data["work_item_type"] == "Bug"
```

- [ ] **Step 3: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py -v'
```

Expected: import errors on the four browse serializer classes.

- [ ] **Step 4: Create the browse serializers**

Create `api/integrations/azure_devops/serializers/browse.py` with the following exact contents:

```python
from rest_framework import serializers

_PR_STATE_CHOICES = ("active", "completed", "abandoned", "all")


class AdoBrowseQueryParamsSerializer(serializers.Serializer[None]):
    top = serializers.IntegerField(default=100, min_value=1, max_value=200)
    continuation_token = serializers.CharField(required=False, allow_blank=True)


class AdoRepositoriesQueryParamsSerializer(AdoBrowseQueryParamsSerializer):
    ado_project_id = serializers.CharField()


class AdoPullRequestsQueryParamsSerializer(AdoRepositoriesQueryParamsSerializer):
    state = serializers.ChoiceField(choices=_PR_STATE_CHOICES, default="active")


class AdoWorkItemsQueryParamsSerializer(AdoRepositoriesQueryParamsSerializer):
    search_text = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    work_item_type = serializers.CharField(required=False, allow_blank=True)
```

(`AdoBrowseQueryParamsSerializer` is the bare paging shape used by `BrowseAdoProjects` which doesn't require an `ado_project_id`. The other three inherit from `AdoRepositoriesQueryParamsSerializer` to share the `ado_project_id` field.)

- [ ] **Step 5: Run tests, mypy, lint, commit**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py -v'
make typecheck
make lint
```

Expected: all clean.

```bash
git add api/integrations/azure_devops/serializers/ api/tests/unit/integrations/azure_devops/test_serializers.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps browse query-param serializers

Four DRF serializers covering paging + per-resource filter shapes:
- AdoBrowseQueryParamsSerializer: paging only (projects browse).
- AdoRepositoriesQueryParamsSerializer: + ado_project_id.
- AdoPullRequestsQueryParamsSerializer: + state (choice-validated).
- AdoWorkItemsQueryParamsSerializer: + search_text, state, work_item_type.

The existing AzureDevOpsConfigurationSerializer moves to
serializers/__init__.py so the `from integrations.azure_devops.serializers
import X` path keeps working for PR 2's viewset and tests.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Browse views

**Files:**
- Create: `api/integrations/azure_devops/views/browse_azure_devops.py`
- Modify: `api/integrations/azure_devops/views/__init__.py`
- Create: `api/tests/unit/integrations/azure_devops/test_browse_views.py`

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_browse_views.py` with the following exact contents:

```python
import responses
from rest_framework import status
from rest_framework.test import APIClient

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project

ORG_URL = "https://dev.azure.com/test-org"
ADO_PROJECT_ID = "00000000-0000-0000-0000-0000000000aa"


@responses.activate
def test_browse_projects__valid__returns_results_and_next_url(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={
            "value": [
                {"id": ADO_PROJECT_ID, "name": "Proj", "url": "ado-url"},
            ],
            "count": 1,
        },
        headers={"x-ms-continuationtoken": "ct-next"},
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"] == [{"id": ADO_PROJECT_ID, "name": "Proj", "url": "ado-url"}]
    assert "continuation_token=ct-next" in body["next"]


@responses.activate
def test_browse_projects__no_configuration__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given — no AzureDevOpsConfiguration for this project

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@responses.activate
def test_browse_projects__ado_unreachable__returns_503(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=500)

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@responses.activate
def test_browse_repositories__valid__returns_typed_list(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        f"{ORG_URL}/{ADO_PROJECT_ID}/_apis/git/repositories",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000bb1",
                    "name": "frontend",
                    "defaultBranch": "refs/heads/main",
                }
            ],
            "count": 1,
        },
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/repositories/"
        f"?ado_project_id={ADO_PROJECT_ID}"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"] == [
        {
            "id": "00000000-0000-0000-0000-000000000bb1",
            "name": "frontend",
            "default_branch": "refs/heads/main",
        }
    ]


def test_browse_repositories__missing_ado_project_id__returns_400(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/repositories/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@responses.activate
def test_browse_pull_requests__default_state__returns_active_prs(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        f"{ORG_URL}/{ADO_PROJECT_ID}/_apis/git/pullrequests",
        json={
            "value": [
                {
                    "pullRequestId": 42,
                    "title": "Add X",
                    "status": "active",
                    "isDraft": False,
                    "repository": {"name": "frontend"},
                    "_links": {
                        "web": {
                            "href": "https://dev.azure.com/test-org/proj/_git/frontend/pullrequest/42"
                        }
                    },
                }
            ],
            "count": 1,
        },
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/pull-requests/"
        f"?ado_project_id={ADO_PROJECT_ID}"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"][0]["id"] == 42


@responses.activate
def test_browse_work_items__title_search__returns_hydrated_items(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.post(
        f"{ORG_URL}/{ADO_PROJECT_ID}/_apis/wit/wiql",
        json={"workItems": [{"id": 101}]},
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 101,
                    "fields": {
                        "System.Title": "Login broken",
                        "System.State": "Active",
                        "System.WorkItemType": "Bug",
                    },
                    "_links": {
                        "html": {
                            "href": "https://dev.azure.com/test-org/proj/_workitems/edit/101"
                        }
                    },
                }
            ]
        },
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/work-items/"
        f"?ado_project_id={ADO_PROJECT_ID}&search_text=login&state=Active&work_item_type=Bug"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"][0]["id"] == 101


def test_browse_projects__unauthenticated__returns_unauthorised(
    api_client: APIClient,
    project: Project,
) -> None:
    # Given

    # When
    response = api_client.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_browse_views.py -v'
```

Expected: 404s or import errors at collection.

- [ ] **Step 3: Create the browse views**

Create `api/integrations/azure_devops/views/browse_azure_devops.py` with the following exact contents:

```python
import abc
from typing import Any, Generic, TypeVar

import requests
import structlog
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from structlog.typing import FilteringBoundLogger

from integrations.azure_devops.client import (
    list_projects,
    list_pull_requests,
    list_repositories,
    list_work_items,
)
from integrations.azure_devops.client.exceptions import AzureDevOpsAuthError
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers.browse import (
    AdoBrowseQueryParamsSerializer,
    AdoPullRequestsQueryParamsSerializer,
    AdoRepositoriesQueryParamsSerializer,
    AdoWorkItemsQueryParamsSerializer,
)
from projects.permissions import NestedProjectPermissions

logger = structlog.get_logger("azure_devops")

T = TypeVar("T")


class _AdoListView(ListAPIView, abc.ABC):  # type: ignore[type-arg]
    permission_classes = [NestedProjectPermissions]
    serializer_class: type[Serializer[Any]] = AdoBrowseQueryParamsSerializer
    action = "list"  # NestedProjectPermissions reads from ViewSet.action

    @abc.abstractmethod
    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        """Return (results, next_continuation_token)."""

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        try:
            config = self._get_config()
        except AzureDevOpsConfiguration.DoesNotExist:
            return Response(
                data={"detail": "This project has no Azure DevOps configuration"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            results, next_token = self.fetch(config, serializer.validated_data)
        except AzureDevOpsAuthError:
            return Response(
                data={"detail": "Azure DevOps rejected the credentials"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        except requests.RequestException as exc:
            self._log_for(config).error("api_call.failed", exc_info=exc)
            return Response(
                data={"detail": "Azure DevOps API is unreachable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return self._paginated_response(results, next_token, request)

    def _log_for(self, config: AzureDevOpsConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            organisation__id=config.project.organisation_id,
            project__id=config.project.id,
        )

    def _get_config(self) -> AzureDevOpsConfiguration:
        return AzureDevOpsConfiguration.objects.get(  # type: ignore[no-any-return]
            project_id=self.kwargs["project_pk"],
            deleted_at__isnull=True,
        )

    def _paginated_response(
        self,
        results: list[dict[str, Any]],
        next_token: str | None,
        request: Request,
    ) -> Response:
        next_url: str | None = None
        if next_token:
            params = request.query_params.copy()
            params["continuation_token"] = next_token
            next_url = request.build_absolute_uri(
                f"{request.path}?{params.urlencode()}"
            )
        return Response(
            {
                "results": results,
                "next": next_url,
                "previous": None,
            }
        )


class BrowseAdoProjects(_AdoListView):
    serializer_class = AdoBrowseQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        page = list_projects(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            top=validated_data["top"],
            continuation_token=validated_data.get("continuation_token"),
        )
        self._log_for(config).info("projects.fetched")
        return list(page["results"]), page["continuation_token"]


class BrowseAdoRepositories(_AdoListView):
    serializer_class = AdoRepositoriesQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        repos = list_repositories(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            ado_project_id=validated_data["ado_project_id"],
        )
        self._log_for(config).info(
            "repositories.fetched",
            ado__project__id=validated_data["ado_project_id"],
        )
        # Repositories endpoint isn't paginated by ADO; expose all in one go.
        return list(repos), None


class BrowseAdoPullRequests(_AdoListView):
    serializer_class = AdoPullRequestsQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        page = list_pull_requests(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            ado_project_id=validated_data["ado_project_id"],
            state=validated_data["state"],
            top=validated_data["top"],
            continuation_token=validated_data.get("continuation_token"),
        )
        self._log_for(config).info(
            "pull_requests.fetched",
            ado__project__id=validated_data["ado_project_id"],
        )
        return list(page["results"]), page["continuation_token"]


class BrowseAdoWorkItems(_AdoListView):
    serializer_class = AdoWorkItemsQueryParamsSerializer

    def fetch(
        self,
        config: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str | None]:
        page = list_work_items(
            organisation_url=config.organisation_url,
            pat=config.personal_access_token,
            ado_project_id=validated_data["ado_project_id"],
            search_text=validated_data.get("search_text") or None,
            state=validated_data.get("state") or None,
            work_item_type=validated_data.get("work_item_type") or None,
            top=validated_data["top"],
            continuation_token=validated_data.get("continuation_token"),
        )
        self._log_for(config).info(
            "work_items.fetched",
            ado__project__id=validated_data["ado_project_id"],
        )
        return list(page["results"]), page["continuation_token"]
```

Then update `api/integrations/azure_devops/views/__init__.py`:

```python
from integrations.azure_devops.views.browse_azure_devops import (
    BrowseAdoProjects,
    BrowseAdoPullRequests,
    BrowseAdoRepositories,
    BrowseAdoWorkItems,
)
from integrations.azure_devops.views.configuration import (
    AzureDevOpsConfigurationViewSet,
)

__all__ = [
    "AzureDevOpsConfigurationViewSet",
    "BrowseAdoProjects",
    "BrowseAdoPullRequests",
    "BrowseAdoRepositories",
    "BrowseAdoWorkItems",
]
```

- [ ] **Step 4: Run tests**

The browse tests will still 404 because URL wiring lands in Task 7. Skip running them for this commit; verify the imports resolve via:

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 5: Lint + commit**

```bash
make lint
```

Expected: clean.

```bash
git add api/integrations/azure_devops/views/browse_azure_devops.py api/integrations/azure_devops/views/__init__.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps browse views (no URL wiring yet)

Four ListAPIView subclasses sharing a _AdoListView base for permission
handling, config lookup, error mapping (400 no config / 502 auth / 503
unreachable), and continuation-token paging. The next commit wires
their URLs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: URL wiring + integration test run

**Files:**
- Modify: `api/projects/urls.py`

- [ ] **Step 1: Add URL paths**

In `api/projects/urls.py`, locate the import block. Find the existing line:

```python
from integrations.azure_devops.views import AzureDevOpsConfigurationViewSet
```

Replace with:

```python
from integrations.azure_devops.views import (
    AzureDevOpsConfigurationViewSet,
    BrowseAdoProjects,
    BrowseAdoPullRequests,
    BrowseAdoRepositories,
    BrowseAdoWorkItems,
)
```

Then locate the GitLab browse-paths block (around lines 154-166 — the `<int:project_pk>/gitlab/projects/` etc. `path()` calls). Add the four ADO browse paths in the same shape, immediately after:

```python
    path(
        "<int:project_pk>/azure-devops/projects/",
        BrowseAdoProjects.as_view(),
        name="get-azure-devops-projects",
    ),
    path(
        "<int:project_pk>/azure-devops/repositories/",
        BrowseAdoRepositories.as_view(),
        name="get-azure-devops-repositories",
    ),
    path(
        "<int:project_pk>/azure-devops/pull-requests/",
        BrowseAdoPullRequests.as_view(),
        name="get-azure-devops-pull-requests",
    ),
    path(
        "<int:project_pk>/azure-devops/work-items/",
        BrowseAdoWorkItems.as_view(),
        name="get-azure-devops-work-items",
    ),
```

If the surrounding `urlpatterns` list shape is different from what you expect, inspect it first and adapt — `urlpatterns` lives at module level and may already be wrapped in a function. The four new paths should be added inside whatever list the GitLab browse paths live in.

- [ ] **Step 2: Run the browse view tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_browse_views.py -v'
```

Expected: 8 passed (across `user` and `master_api_key` parametrisations the count may double).

- [ ] **Step 3: mypy + lint**

```bash
make typecheck
make lint
```

Expected: both clean.

- [ ] **Step 4: Commit**

```bash
git add api/projects/urls.py api/tests/unit/integrations/azure_devops/test_browse_views.py
git commit -m "$(cat <<'EOF'
feat(integrations): wire Azure DevOps browse URLs

Four nested paths under /api/v1/projects/{project_pk}/azure-devops/:
projects, repositories, pull-requests, work-items. Path prefix is
"azure-devops/" (not "integrations/azure-devops/") to mirror the
GitLab precedent and avoid routing conflict with the CRUD viewset's
{pk} capture.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Full-suite verification

- [ ] **Step 1: Lint**

```bash
cd api && make lint
```

Expected: clean.

- [ ] **Step 2: Type check**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 3: Whole new test directory**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/ -v'
```

Expected: every test passes. Approximate count: PR 4 baseline 127 + 5 TypedDicts + 2 list_repositories + 3 list_pull_requests + 6 list_work_items + 8 serializers + 8 browse views (parametrised across auth → likely 16). Around 175.

- [ ] **Step 4: Regression guard**

```bash
make test opts='tests/unit/integrations/gitlab tests/unit/integrations/github tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/features/test_migrations.py'
```

Expected: all pass.

- [ ] **Step 5: Migration consistency**

```bash
make django-make-migrations opts='--check --dry-run'
```

Expected: `No changes detected` — PR 5 introduces no schema changes.

- [ ] **Step 6: Branch state**

```bash
git status
git log --oneline feat/azure-devops-04-tagging..HEAD
```

Expected: working tree clean; 7 feature commits + plan-doc commit on this branch ahead of `feat/azure-devops-04-tagging`.

---

## Done condition

- Branch `feat/azure-devops-05-browse` carries the PR 5 plan-doc commit plus seven feature commits.
- The Azure DevOps REST client gains `list_repositories`, `list_pull_requests`, `list_work_items`.
- Four browse endpoints live under `/api/v1/projects/{flagsmith_project_id}/azure-devops/`.
- The serializers module is split into a subpackage (`serializers/__init__.py` for configuration; `serializers/browse.py` for browse query params).
- All new tests pass; mypy strict, ruff, `flagsmith-lint-tests` clean.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-04-tagging`.
