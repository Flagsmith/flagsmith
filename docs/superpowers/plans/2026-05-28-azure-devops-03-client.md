# Azure DevOps Integration — PR 3: REST client, URL parsing, PAT validation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Azure DevOps REST client (limited to `list_projects` for v1), URL parsing for PR and work-item URLs, `organisation_url` normalisation on the model, and wire PAT validation into the configuration viewset so create/update calls verify credentials against ADO before persisting.

**Architecture:** Mirror the GitLab client's layout (`client/api.py`, `client/types.py`, plus a new `client/exceptions.py` for typed exceptions ADO needs). HTTP auth is Basic with empty username and PAT as password — the ADO convention. URL parsing returns `NamedTuple` refs for both PR and work-item URLs across cloud (`dev.azure.com/{org}`) and on-prem (`{host}/{collection}`) shapes. PAT validation lives in the viewset; the `responses` library is used to mock the upstream ADO probe in tests.

**Tech Stack:** Python 3.12, Django 5.x, DRF, `requests`, `responses` (test-only), pytest with `pytest-django`, mypy strict.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Components → `client/api.py`", "Components → `client/types.py`", "Components → `services/url_parsing.py`", "Components → `views/configuration.py`", "Error handling → Bad PAT at save time", "Data model → AzureDevOpsConfiguration → organisation_url normalisation".

**Plan reference (parent):** `docs/superpowers/plans/2026-05-28-azure-devops-02-models.md`.

**Stack position:** PR 3 of N. Branches off `feat/azure-devops-02-models`. Branch name: `feat/azure-devops-03-client`. Will PR against `feat/azure-devops-02-models` initially; retargeted at `main` after PR 1 and PR 2 land.

---

## Scope deliberately out of PR 3

- The rest of the client surface (`list_repositories`, `list_pull_requests`, `list_work_items`, comment-posting, label-add/remove, subscription create/delete) — added incrementally by later PRs that need them. PR 3 only lands what PAT validation actually requires.
- Microsoft Entra OAuth — PAT only.
- Encryption at rest for the PAT — still deferred (matches the PR 2 scope-out).
- ADO API request-duration metric (`flagsmith_azure_devops_api_request_duration_seconds`) — added in PR 12 with the rest of `metrics.py`.

---

## File Structure

- **Create:** `api/integrations/azure_devops/constants.py` — `AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS`, the `_apis/projects?$top=1` probe path.
- **Create:** `api/integrations/azure_devops/client/__init__.py` — re-exports the client's public surface (`list_projects`, the exceptions, the typed dicts).
- **Create:** `api/integrations/azure_devops/client/types.py` — `AdoProject`, `AdoProjectsPage`.
- **Create:** `api/integrations/azure_devops/client/exceptions.py` — `AzureDevOpsError`, `AzureDevOpsAuthError`, `AzureDevOpsNotFoundError`.
- **Create:** `api/integrations/azure_devops/client/api.py` — `list_projects` + HTTP plumbing helper.
- **Create:** `api/integrations/azure_devops/services/__init__.py` — empty package marker.
- **Create:** `api/integrations/azure_devops/services/url_parsing.py` — `parse_pull_request_url`, `parse_work_item_url`, the `AdoPullRequestRef` / `AdoWorkItemRef` NamedTuples.
- **Modify:** `api/integrations/azure_devops/models.py` — add `save()` override on `AzureDevOpsConfiguration` that strips trailing slash from `organisation_url`.
- **Modify:** `api/integrations/azure_devops/serializers.py` — override `update()` so a `personal_access_token` equal to `WRITE_ONLY_PLACEHOLDER` on input is dropped from validated data (preserves existing PAT).
- **Modify:** `api/integrations/azure_devops/views/configuration.py` — `perform_create` and `perform_update` call a new `_validate_pat_against_ado(organisation_url, pat)` helper; on `AzureDevOpsAuthError` raise a DRF `ValidationError("Azure DevOps rejected the credentials.")`.
- **Create:** `api/tests/unit/integrations/azure_devops/test_exceptions.py` — exception hierarchy tests.
- **Create:** `api/tests/unit/integrations/azure_devops/test_client.py` — client behaviour tests (auth header, status mapping, timeout).
- **Create:** `api/tests/unit/integrations/azure_devops/test_url_parsing.py` — parametrised URL parsing.
- **Modify:** `api/tests/unit/integrations/azure_devops/test_models.py` — add `save()` normalisation tests.
- **Modify:** `api/tests/unit/integrations/azure_devops/test_serializers.py` — add placeholder-preservation tests.
- **Modify:** `api/tests/unit/integrations/azure_devops/test_configuration.py` — add `@responses.activate` and ADO mocks to the three tests that exercise `perform_create` / `perform_update`; add new tests for invalid-PAT and placeholder-on-update.

No other files are touched in this PR.

---

## Pre-flight

- [ ] **Step 0: Confirm working branch**

```bash
cd /Users/asaphkotzin/Dev/flagsmith
git status
git log --oneline -3
```

Expected: branch `feat/azure-devops-03-client`, HEAD is the parent branch's tip (the PR 2 final commit). Working tree clean. If the branch does not exist, create it off `feat/azure-devops-02-models`:

```bash
git checkout feat/azure-devops-02-models
git checkout -b feat/azure-devops-03-client
```

---

## Task 1: Constants and client scaffolding

**Files:**
- Create: `api/integrations/azure_devops/constants.py`
- Create: `api/integrations/azure_devops/client/__init__.py`
- Create: `api/integrations/azure_devops/services/__init__.py`
- Test: a smoke test that the constants import

- [ ] **Step 1: Create the constants module**

Create `api/integrations/azure_devops/constants.py` with the following exact contents:

```python
AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS = 10

AZURE_DEVOPS_API_VERSION = "7.1"
```

(The API version is locked to 7.1, the current stable ADO REST API version. Mirroring GitLab's `GITLAB_CLIENT_TIMEOUT_SECONDS` constant naming.)

- [ ] **Step 2: Create the empty package markers**

```bash
mkdir -p api/integrations/azure_devops/client api/integrations/azure_devops/services
```

Create `api/integrations/azure_devops/client/__init__.py` with contents:

```python
```

(empty)

Create `api/integrations/azure_devops/services/__init__.py` with contents:

```python
```

(empty)

- [ ] **Step 3: Write the smoke test**

Create `api/tests/unit/integrations/azure_devops/test_constants.py` with:

```python
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_API_VERSION,
    AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
)


def test_constants__timeout__has_sensible_default() -> None:
    # Given
    timeout = AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS

    # When
    is_positive_int = isinstance(timeout, int) and timeout > 0

    # Then
    assert is_positive_int
    assert timeout <= 60


def test_constants__api_version__is_string() -> None:
    # Given
    version = AZURE_DEVOPS_API_VERSION

    # When
    is_string = isinstance(version, str)

    # Then
    assert is_string
    assert version
```

- [ ] **Step 4: Run the tests**

From `api/`:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_constants.py -v'
```

Expected: 2 passed.

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/constants.py api/integrations/azure_devops/client/__init__.py api/integrations/azure_devops/services/__init__.py api/tests/unit/integrations/azure_devops/test_constants.py
git commit -m "$(cat <<'EOF'
feat(integrations): scaffold Azure DevOps client + services packages

Add empty client/ and services/ packages plus a constants module holding
the request timeout and pinned REST API version (7.1). Subsequent
commits in this PR fill in the client modules and the URL-parsing
service.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Typed exceptions

**Files:**
- Create: `api/integrations/azure_devops/client/exceptions.py`
- Create: `api/tests/unit/integrations/azure_devops/test_exceptions.py`

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_exceptions.py` with:

```python
import pytest

from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsError,
    AzureDevOpsNotFoundError,
)


def test_azure_devops_auth_error__inheritance__is_subclass_of_base() -> None:
    # Given
    cls = AzureDevOpsAuthError

    # When
    is_subclass = issubclass(cls, AzureDevOpsError)

    # Then
    assert is_subclass


def test_azure_devops_not_found_error__inheritance__is_subclass_of_base() -> None:
    # Given
    cls = AzureDevOpsNotFoundError

    # When
    is_subclass = issubclass(cls, AzureDevOpsError)

    # Then
    assert is_subclass


def test_azure_devops_error__base__is_exception_subclass() -> None:
    # Given
    cls = AzureDevOpsError

    # When
    is_exception = issubclass(cls, Exception)

    # Then
    assert is_exception


def test_azure_devops_auth_error__raise_and_catch__as_base_works() -> None:
    # Given
    def raise_auth_error() -> None:
        raise AzureDevOpsAuthError("invalid PAT")

    # When
    with pytest.raises(AzureDevOpsError) as exc_info:
        raise_auth_error()

    # Then
    assert "invalid PAT" in str(exc_info.value)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_exceptions.py -v'
```

Expected: import error — module not found.

- [ ] **Step 3: Create the exceptions module**

Create `api/integrations/azure_devops/client/exceptions.py` with the following exact contents:

```python
class AzureDevOpsError(Exception):
    """Base class for all Azure DevOps client errors raised by this package."""


class AzureDevOpsAuthError(AzureDevOpsError):
    """Raised when ADO rejects credentials with 401 or 403."""


class AzureDevOpsNotFoundError(AzureDevOpsError):
    """Raised when ADO returns 404 for a single-resource lookup."""
```

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_exceptions.py -v'
```

Expected: 4 passed.

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/client/exceptions.py api/tests/unit/integrations/azure_devops/test_exceptions.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps client typed exceptions

Three classes: AzureDevOpsError (base), AzureDevOpsAuthError (401/403),
AzureDevOpsNotFoundError (404 on single-resource). Callers can catch
the base for "anything went wrong with ADO" or the specific subclass
for targeted handling.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Client types

**Files:**
- Create: `api/integrations/azure_devops/client/types.py`
- Test: extends `api/tests/unit/integrations/azure_devops/test_client.py` indirectly when the client is added in Task 4

For PR 3 we only need `AdoProject` and a `AdoProjectsPage` page-shape for `list_projects`. Later PRs will extend this module with `AdoRepository`, `AdoPullRequest`, `AdoWorkItem`, `AdoSubscription`, and the resource-metadata typed dict.

- [ ] **Step 1: Create the types module**

Create `api/integrations/azure_devops/client/types.py` with the following exact contents:

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

(The `id` field is `str` because ADO project GUIDs come over the wire as strings. We can cast to `uuid.UUID` at consumption time where typed; the client stays representation-faithful.)

- [ ] **Step 2: Write a smoke test**

Append to `api/tests/unit/integrations/azure_devops/test_client.py` (creating the file at this point even though Task 4 will append more):

```python
from integrations.azure_devops.client.types import AdoProject, AdoProjectsPage


def test_ado_project__shape__has_required_keys() -> None:
    # Given
    project: AdoProject = {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "Test",
        "url": "https://dev.azure.com/test-org/_apis/projects/...",
    }

    # When
    keys = set(project.keys())

    # Then
    assert keys == {"id", "name", "url"}


def test_ado_projects_page__shape__has_required_keys() -> None:
    # Given
    page: AdoProjectsPage = {"results": [], "continuation_token": None}

    # When
    keys = set(page.keys())

    # Then
    assert keys == {"results", "continuation_token"}
```

- [ ] **Step 3: Run the test**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
```

Expected: 2 passed.

- [ ] **Step 4: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add api/integrations/azure_devops/client/types.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps client TypedDicts

Two typed dicts for v1: AdoProject (id/name/url) and AdoProjectsPage
(results + continuation_token). Subsequent PRs will extend this module
with AdoRepository, AdoPullRequest, AdoWorkItem, AdoSubscription, and
the resource-metadata shape as their corresponding client functions
land.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Client `list_projects` + HTTP plumbing

**Files:**
- Modify: `api/integrations/azure_devops/client/__init__.py` (re-export the function)
- Create: `api/integrations/azure_devops/client/api.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py` (append client behaviour tests)

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
import base64

import pytest
import requests
import responses

from integrations.azure_devops.client import list_projects
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)

ORG_URL = "https://dev.azure.com/test-org"
PAT = "ado-test-pat"


def _expected_basic_auth_header() -> str:
    # ADO PAT auth: HTTP Basic with empty username and PAT as password.
    encoded = base64.b64encode(f":{PAT}".encode()).decode()
    return f"Basic {encoded}"


@responses.activate
def test_list_projects__valid_response__returns_typed_page() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "Alpha",
                    "url": f"{ORG_URL}/_apis/projects/00000000-0000-0000-0000-000000000001",
                    "extra": "ignored",
                },
            ],
            "count": 1,
        },
        match=[
            responses.matchers.header_matcher(
                {"Authorization": _expected_basic_auth_header()}
            )
        ],
    )

    # When
    page = list_projects(organisation_url=ORG_URL, pat=PAT, top=1)

    # Then
    assert page["results"] == [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Alpha",
            "url": f"{ORG_URL}/_apis/projects/00000000-0000-0000-0000-000000000001",
        },
    ]
    assert page["continuation_token"] is None


@responses.activate
def test_list_projects__continuation_token_in_header__exposed_on_page() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={"value": [], "count": 0},
        headers={"x-ms-continuationtoken": "ct-abc"},
    )

    # When
    page = list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    assert page["continuation_token"] == "ct-abc"


@responses.activate
def test_list_projects__401_response__raises_auth_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=401)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    with pytest.raises(AzureDevOpsAuthError):
        call_list()


@responses.activate
def test_list_projects__403_response__raises_auth_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=403)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    with pytest.raises(AzureDevOpsAuthError):
        call_list()


@responses.activate
def test_list_projects__404_response__raises_not_found_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=404)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    with pytest.raises(AzureDevOpsNotFoundError):
        call_list()


@responses.activate
def test_list_projects__500_response__raises_requests_http_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=500)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then — non-4xx server failures bubble up as the underlying requests error
    with pytest.raises(requests.HTTPError):
        call_list()


@responses.activate
def test_list_projects__trailing_slash_in_org_url__normalised_in_request() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={"value": [], "count": 0},
    )

    # When
    list_projects(organisation_url=f"{ORG_URL}/", pat=PAT)

    # Then — request lands on ORG_URL/_apis/projects (no double slash)
    assert responses.calls[0].request.url is not None
    assert "//_apis" not in responses.calls[0].request.url
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
```

Expected: collection-level failures — `list_projects` not importable from `integrations.azure_devops.client`.

- [ ] **Step 3: Create the client module**

Create `api/integrations/azure_devops/client/api.py` with the following exact contents:

```python
from typing import Any

import requests

from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import AdoProject, AdoProjectsPage
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_API_VERSION,
    AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
)


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
        auth=("", pat),
        params=query,
        json=json_body,
        timeout=AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
    )
    if response.status_code in (401, 403):
        raise AzureDevOpsAuthError(
            f"Azure DevOps rejected credentials ({response.status_code})"
        )
    if response.status_code == 404:
        raise AzureDevOpsNotFoundError(
            f"Azure DevOps reported the resource was not found ({response.status_code})"
        )
    response.raise_for_status()
    return response


def list_projects(
    *,
    organisation_url: str,
    pat: str,
    top: int | None = None,
    continuation_token: str | None = None,
) -> AdoProjectsPage:
    params: dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if continuation_token is not None:
        params["continuationToken"] = continuation_token

    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path="projects",
        params=params,
    )
    payload = response.json()
    results: list[AdoProject] = [
        AdoProject(id=p["id"], name=p["name"], url=p["url"])
        for p in payload.get("value", [])
    ]
    next_token = response.headers.get("x-ms-continuationtoken")
    return AdoProjectsPage(results=results, continuation_token=next_token)
```

(Notes on the implementation:
- `auth=("", pat)` is the ADO PAT convention — HTTP Basic with empty username and PAT as password.
- `api-version` is always passed as a query parameter — required by ADO for every REST call.
- `_ado_request` is the single chokepoint where status mapping happens. 401/403 → `AzureDevOpsAuthError`. 404 → `AzureDevOpsNotFoundError`. 5xx and other 4xx → `requests.HTTPError`.
- `organisation_url.rstrip("/")` is defensive — the model normalises this at save time, but a caller passing an unnormalised URL still gets a correctly-formed request.)

- [ ] **Step 4: Re-export the public surface from the client package**

Replace `api/integrations/azure_devops/client/__init__.py` (currently empty) with:

```python
from integrations.azure_devops.client.api import list_projects
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import AdoProject, AdoProjectsPage

__all__ = [
    "AdoProject",
    "AdoProjectsPage",
    "AzureDevOpsAuthError",
    "AzureDevOpsError",
    "AzureDevOpsNotFoundError",
    "list_projects",
]
```

- [ ] **Step 5: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
```

Expected: 9 passed (2 from Task 3 + 7 new).

- [ ] **Step 6: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/client/api.py api/integrations/azure_devops/client/__init__.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add list_projects to the Azure DevOps client

Stand up the client's HTTP plumbing (Basic auth with empty username,
api-version=7.1 query param, 10s timeout) and the first concrete
function: list_projects. Status codes 401/403 map to AzureDevOpsAuthError,
404 to AzureDevOpsNotFoundError; 5xx and other 4xx bubble up as
requests.HTTPError. Subsequent client functions (repos, PRs, work items,
comments, labels, subscriptions) land in their respective consumer PRs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: URL parsing

**Files:**
- Create: `api/integrations/azure_devops/services/url_parsing.py`
- Create: `api/tests/unit/integrations/azure_devops/test_url_parsing.py`

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_url_parsing.py` with the following exact contents:

```python
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
    # Given / When
    result = parse_pull_request_url(url)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://github.com/foo/bar/pull/42",  # GitHub
        "https://gitlab.com/foo/bar/-/merge_requests/42",  # GitLab
        "https://dev.azure.com/test-org/proj/_git/repo",  # missing /pullrequest/{id}
        "https://dev.azure.com/test-org/proj/_workitems/edit/42",  # work item, not PR
        "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/not-a-number",
    ],
)
def test_parse_pull_request_url__malformed_or_other_shapes__returns_none(url: str) -> None:
    # Given / When
    result = parse_pull_request_url(url)

    # Then
    assert result is None


@pytest.mark.parametrize(
    "url, expected",
    [
        # Cloud, plain
        (
            "https://dev.azure.com/test-org/proj/_workitems/edit/100",
            AdoWorkItemRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                work_item_id=100,
            ),
        ),
        # Cloud, trailing slash
        (
            "https://dev.azure.com/test-org/proj/_workitems/edit/100/",
            AdoWorkItemRef(
                organisation_root="https://dev.azure.com/test-org",
                project="proj",
                work_item_id=100,
            ),
        ),
        # Cloud, URL-encoded project name
        (
            "https://dev.azure.com/test-org/My%20Project/_workitems/edit/7",
            AdoWorkItemRef(
                organisation_root="https://dev.azure.com/test-org",
                project="My Project",
                work_item_id=7,
            ),
        ),
        # On-prem with collection
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
    # Given / When
    result = parse_work_item_url(url)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not-a-url",
        "https://github.com/foo/bar/issues/42",
        "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42",  # PR, not work item
        "https://dev.azure.com/test-org/proj/_workitems/edit/not-a-number",
    ],
)
def test_parse_work_item_url__malformed_or_other_shapes__returns_none(url: str) -> None:
    # Given / When
    result = parse_work_item_url(url)

    # Then
    assert result is None
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_url_parsing.py -v'
```

Expected: import errors — `parse_pull_request_url`, `AdoPullRequestRef`, etc. not defined.

- [ ] **Step 3: Create the URL parser**

Create `api/integrations/azure_devops/services/url_parsing.py` with the following exact contents:

```python
import re
from typing import NamedTuple
from urllib.parse import unquote, urlparse

# Path captures (after stripping query/fragment, normalising trailing slash):
#   /{org_or_collection}/{project}/_git/{repo}/pullrequest/{id}
#   /{org_or_collection}/{project}/_workitems/edit/{id}
#
# For ADO cloud, {org_or_collection} is a single org segment (e.g. "test-org").
# For Azure DevOps Server (on-prem), {org_or_collection} is a collection name,
# and the same path pattern applies under whatever host the server runs on.

_PR_PATH_PATTERN = re.compile(
    r"^/(?P<org_or_collection>[^/]+)/(?P<project>[^/]+)"
    r"/_git/(?P<repo>[^/]+)/pullrequest/(?P<pr_id>\d+)/?$"
)

_WORK_ITEM_PATH_PATTERN = re.compile(
    r"^/(?P<org_or_collection>[^/]+)/(?P<project>[^/]+)"
    r"/_workitems/edit/(?P<work_item_id>\d+)/?$"
)


class AdoPullRequestRef(NamedTuple):
    organisation_root: str
    project: str
    repository: str
    pull_request_id: int


class AdoWorkItemRef(NamedTuple):
    organisation_root: str
    project: str
    work_item_id: int


def parse_pull_request_url(url: str | None) -> AdoPullRequestRef | None:
    """Return a structured reference for an Azure DevOps pull-request URL,
    or ``None`` if the URL does not match the cloud or on-prem PR shape.
    Parsing never raises.
    """
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    match = _PR_PATH_PATTERN.match(parsed.path)
    if not match:
        return None
    return AdoPullRequestRef(
        organisation_root=f"{parsed.scheme}://{parsed.netloc}/{match.group('org_or_collection')}",
        project=unquote(match.group("project")),
        repository=unquote(match.group("repo")),
        pull_request_id=int(match.group("pr_id")),
    )


def parse_work_item_url(url: str | None) -> AdoWorkItemRef | None:
    """Return a structured reference for an Azure DevOps work-item URL,
    or ``None`` if the URL does not match the cloud or on-prem work-item
    shape. Parsing never raises.
    """
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    match = _WORK_ITEM_PATH_PATTERN.match(parsed.path)
    if not match:
        return None
    return AdoWorkItemRef(
        organisation_root=f"{parsed.scheme}://{parsed.netloc}/{match.group('org_or_collection')}",
        project=unquote(match.group("project")),
        work_item_id=int(match.group("work_item_id")),
    )
```

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_url_parsing.py -v'
```

Expected: all parametrised cases pass.

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/services/url_parsing.py api/tests/unit/integrations/azure_devops/test_url_parsing.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps URL parsing for PRs and work items

Two NamedTuple types (AdoPullRequestRef, AdoWorkItemRef) and two parser
functions that handle both ADO cloud (dev.azure.com/{org}/...) and
Azure DevOps Server (host/{collection}/...) URL shapes. Parsing never
raises; unparseable URLs return None. Subsequent PRs (browse, comments,
webhook dispatcher) use these structured refs instead of raw URL string
comparisons.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: `organisation_url` normalisation on save

**Files:**
- Modify: `api/integrations/azure_devops/models.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_models.py`

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_models.py`:

```python
@pytest.mark.django_db
def test_azure_devops_configuration__save__strips_single_trailing_slash(
    project: Project,
) -> None:
    # Given
    raw_url = "https://dev.azure.com/test-org/"

    # When
    config = AzureDevOpsConfiguration.objects.create(
        project=project,
        organisation_url=raw_url,
        personal_access_token="ado-test-token",
    )

    # Then
    assert config.organisation_url == "https://dev.azure.com/test-org"


@pytest.mark.django_db
def test_azure_devops_configuration__save__strips_multiple_trailing_slashes(
    project: Project,
) -> None:
    # Given
    raw_url = "https://dev.azure.com/test-org///"

    # When
    config = AzureDevOpsConfiguration.objects.create(
        project=project,
        organisation_url=raw_url,
        personal_access_token="ado-test-token",
    )

    # Then
    assert config.organisation_url == "https://dev.azure.com/test-org"


@pytest.mark.django_db
def test_azure_devops_configuration__save__no_trailing_slash__is_unchanged(
    project: Project,
) -> None:
    # Given
    raw_url = "https://dev.azure.com/test-org"

    # When
    config = AzureDevOpsConfiguration.objects.create(
        project=project,
        organisation_url=raw_url,
        personal_access_token="ado-test-token",
    )

    # Then
    assert config.organisation_url == raw_url
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_models.py -v'
```

Expected: the three new tests fail because URL is stored verbatim with trailing slashes today.

- [ ] **Step 3: Add the `save()` override**

In `api/integrations/azure_devops/models.py`, modify the `AzureDevOpsConfiguration` class. The model currently looks like:

```python
class AzureDevOpsConfiguration(SoftDeleteExportableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="azure_devops_config",
    )
    organisation_url = models.URLField(max_length=300)
    personal_access_token = models.CharField(max_length=300)
    labeling_enabled = models.BooleanField(default=False)
    tagging_enabled = models.BooleanField(default=False)
```

Add the `save()` override at the bottom of the class:

```python
class AzureDevOpsConfiguration(SoftDeleteExportableModel):
    project = models.OneToOneField(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="azure_devops_config",
    )
    organisation_url = models.URLField(max_length=300)
    personal_access_token = models.CharField(max_length=300)
    labeling_enabled = models.BooleanField(default=False)
    tagging_enabled = models.BooleanField(default=False)

    def save(self, *args: object, **kwargs: object) -> None:
        self.organisation_url = self.organisation_url.rstrip("/")
        super().save(*args, **kwargs)
```

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_models.py -v'
```

Expected: all model tests pass (6 from Task 2 + 3 from Task 3 + 3 new = 12).

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean. (The `*args: object, **kwargs: object` signature is intentionally permissive — `SoftDeleteExportableModel.save` accepts arbitrary args/kwargs.)

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/models.py api/tests/unit/integrations/azure_devops/test_models.py
git commit -m "$(cat <<'EOF'
feat(integrations): normalise organisation_url on save

Strip trailing slashes from AzureDevOpsConfiguration.organisation_url
before persisting. This guarantees downstream URL composition
(client.api._ado_request) never produces double-slash paths regardless
of how the user supplied the URL.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Serializer drops placeholder PAT on update

**Files:**
- Modify: `api/integrations/azure_devops/serializers.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_serializers.py`

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_serializers.py`:

```python
from typing import cast


@pytest.mark.django_db
def test_serializer__update_with_placeholder_pat__preserves_existing_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    original_token = azure_devops_configuration.personal_access_token
    serializer = AzureDevOpsConfigurationSerializer(
        instance=azure_devops_configuration,
        data={
            "organisation_url": azure_devops_configuration.organisation_url,
            "personal_access_token": WRITE_ONLY_PLACEHOLDER,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    cast(AzureDevOpsConfigurationSerializer, serializer).save()

    # Then
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == original_token


@pytest.mark.django_db
def test_serializer__update_with_new_pat__persists_new_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    new_token = "ado-rotated-token"
    serializer = AzureDevOpsConfigurationSerializer(
        instance=azure_devops_configuration,
        data={
            "organisation_url": azure_devops_configuration.organisation_url,
            "personal_access_token": new_token,
        },
    )

    # When
    serializer.is_valid(raise_exception=True)
    cast(AzureDevOpsConfigurationSerializer, serializer).save()

    # Then
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == new_token
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py -v'
```

Expected: the first new test fails — the placeholder is currently persisted as the new token; the original token is overwritten.

- [ ] **Step 3: Override `update()` on the serializer**

In `api/integrations/azure_devops/serializers.py`, the serializer currently looks like:

```python
from typing import Any

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.common.serializers import BaseProjectIntegrationModelSerializer

WRITE_ONLY_PLACEHOLDER = "write-only"


class AzureDevOpsConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = AzureDevOpsConfiguration
        fields = (
            "id",
            "organisation_url",
            "personal_access_token",
            "labeling_enabled",
            "tagging_enabled",
        )

    def to_representation(self, instance: AzureDevOpsConfiguration) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["personal_access_token"] = WRITE_ONLY_PLACEHOLDER
        return data
```

Add the `update()` override:

```python
from typing import Any

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.common.serializers import BaseProjectIntegrationModelSerializer

WRITE_ONLY_PLACEHOLDER = "write-only"


class AzureDevOpsConfigurationSerializer(BaseProjectIntegrationModelSerializer):
    class Meta:
        model = AzureDevOpsConfiguration
        fields = (
            "id",
            "organisation_url",
            "personal_access_token",
            "labeling_enabled",
            "tagging_enabled",
        )

    def to_representation(self, instance: AzureDevOpsConfiguration) -> dict[str, Any]:
        data = super().to_representation(instance)
        data["personal_access_token"] = WRITE_ONLY_PLACEHOLDER
        return data

    def update(
        self,
        instance: AzureDevOpsConfiguration,
        validated_data: dict[str, Any],
    ) -> AzureDevOpsConfiguration:
        # Treat the masked placeholder on input as "no change" so the
        # frontend can round-trip the masked representation without
        # accidentally overwriting the real PAT.
        if validated_data.get("personal_access_token") == WRITE_ONLY_PLACEHOLDER:
            validated_data.pop("personal_access_token", None)
        return super().update(instance, validated_data)  # type: ignore[no-any-return]
```

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py -v'
```

Expected: 3 passed (1 from Task 4 of PR 2 + 2 new).

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/serializers.py api/tests/unit/integrations/azure_devops/test_serializers.py
git commit -m "$(cat <<'EOF'
feat(integrations): preserve PAT on update when payload sends placeholder

Override the serializer's update() to drop personal_access_token from
validated_data when its value equals WRITE_ONLY_PLACEHOLDER. This lets
the frontend safely round-trip the masked representation without
overwriting the stored PAT, and keeps the imminent PAT-validation hook
in the viewset from validating a sentinel string against ADO.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Wire PAT validation into the configuration viewset

**Files:**
- Modify: `api/integrations/azure_devops/views/configuration.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_configuration.py`

This task adds the validation call **and** updates the three existing tests in `test_configuration.py` that exercise `perform_create` / `perform_update` to mock the ADO probe via `responses`.

- [ ] **Step 1: Write the new failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_configuration.py`:

```python
import responses


@responses.activate
def test_create_configuration__invalid_pat__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/test-org/_apis/projects",
        json={},
        status=401,
    )
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-bogus-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Azure DevOps rejected" in str(response.json())
    assert not AzureDevOpsConfiguration.objects.filter(project=project).exists()


@responses.activate
def test_update_configuration__placeholder_pat__skips_validation(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given — no ADO probe response registered; if validation runs, the test
    # will fail with a `responses.ConnectionError`.
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )
    payload = {
        "organisation_url": azure_devops_configuration.organisation_url,
        "personal_access_token": "write-only",
        "labeling_enabled": True,
        "tagging_enabled": True,
    }
    original_pat = azure_devops_configuration.personal_access_token

    # When
    response = admin_client_new.put(detail_url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == original_pat
    assert azure_devops_configuration.labeling_enabled is True
    assert azure_devops_configuration.tagging_enabled is True
```

- [ ] **Step 2: Update the existing affected tests to mock the ADO probe**

In `api/tests/unit/integrations/azure_devops/test_configuration.py`, three existing tests need updates because their request paths now invoke the validation helper:

1. `test_create_configuration__valid_data__persists_and_masks_token` — change the function decorator and add a response stub at the start of `# Given`:

```python
@responses.activate
def test_create_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/test-org/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-test-token",
    }
    # ... existing # When / # Then unchanged
```

(Keep the existing assertions verbatim — only add the decorator and the `responses.get(...)` call inside `# Given`.)

2. `test_create_configuration__after_soft_delete__undeletes_existing_row` — same shape: add `@responses.activate` and a 200 stub for `https://dev.azure.com/recreated/_apis/projects`:

```python
@responses.activate
def test_create_configuration__after_soft_delete__undeletes_existing_row(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    original_pk = azure_devops_configuration.pk
    azure_devops_configuration.delete()
    responses.get(
        "https://dev.azure.com/recreated/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/recreated",
        "personal_access_token": "ado-recreated-token",
    }
    # ... existing # When / # Then unchanged
```

3. `test_update_configuration__valid_data__persists_and_masks_token` — add `@responses.activate` and a 200 stub for `https://dev.azure.com/updated/_apis/projects` (the URL after update):

```python
@responses.activate
def test_update_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/updated/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )
    payload = {
        "organisation_url": "https://dev.azure.com/updated",
        "personal_access_token": "ado-updated-token",
        "labeling_enabled": True,
        "tagging_enabled": True,
    }
    # ... existing # When / # Then unchanged
```

- [ ] **Step 3: Run the test file to verify the new tests fail (validation not yet wired)**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_configuration.py -v'
```

Expected outcomes:
- `test_create_configuration__invalid_pat__returns_400` FAIL (no validation → still 201)
- `test_update_configuration__placeholder_pat__skips_validation` FAIL (the existing serializer override drops the placeholder, so the PUT succeeds, but the validation helper doesn't exist yet; this test may actually pass at this stage — that's fine, it's a regression guard)
- The three existing tests should still pass (they have the mock now, but the validation helper isn't called yet)

If everything is green at this stage it just means validation hasn't been wired; that's the next step.

- [ ] **Step 4: Wire the validation helper into the viewset**

In `api/integrations/azure_devops/views/configuration.py`, the file currently has:

```python
import structlog
from structlog.typing import FilteringBoundLogger

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    AzureDevOpsConfigurationSerializer,
)
from integrations.common.views import ProjectIntegrationBaseViewSet

logger = structlog.get_logger("azure_devops")


class AzureDevOpsConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = AzureDevOpsConfigurationSerializer  # type: ignore[assignment]
    model_class = AzureDevOpsConfiguration  # type: ignore[assignment]
    pagination_class = None

    def _log_for(self, config: AzureDevOpsConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            organisation__id=config.project.organisation_id,
            project__id=config.project.id,
        )

    def perform_create(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        super().perform_create(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.created",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_update(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        super().perform_update(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.updated",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_destroy(self, instance: AzureDevOpsConfiguration) -> None:
        log = self._log_for(instance)
        super().perform_destroy(instance)
        log.info("configuration.deleted")
```

Replace it with the following (full file contents):

```python
import structlog
from rest_framework.exceptions import ValidationError
from structlog.typing import FilteringBoundLogger

from integrations.azure_devops.client import list_projects
from integrations.azure_devops.client.exceptions import AzureDevOpsAuthError
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    AzureDevOpsConfigurationSerializer,
)
from integrations.common.views import ProjectIntegrationBaseViewSet

logger = structlog.get_logger("azure_devops")


def _validate_pat_against_ado(*, organisation_url: str, pat: str) -> None:
    """Probe ADO with a minimal request to confirm the PAT is valid.

    Raises ``ValidationError`` on 401/403 from ADO. Other failures (5xx,
    network) bubble up so the caller can decide whether to log-and-allow
    or surface as an error.
    """
    try:
        list_projects(organisation_url=organisation_url, pat=pat, top=1)
    except AzureDevOpsAuthError:
        raise ValidationError(
            "Azure DevOps rejected the credentials. "
            "Check the organisation URL and personal access token."
        ) from None


class AzureDevOpsConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = AzureDevOpsConfigurationSerializer  # type: ignore[assignment]
    model_class = AzureDevOpsConfiguration  # type: ignore[assignment]
    pagination_class = None

    def _log_for(self, config: AzureDevOpsConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            organisation__id=config.project.organisation_id,
            project__id=config.project.id,
        )

    def perform_create(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        _validate_pat_against_ado(
            organisation_url=serializer.validated_data["organisation_url"],
            pat=serializer.validated_data["personal_access_token"],
        )
        super().perform_create(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.created",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_update(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        pat = serializer.validated_data.get("personal_access_token")
        if pat is not None:
            _validate_pat_against_ado(
                organisation_url=serializer.validated_data.get(
                    "organisation_url",
                    serializer.instance.organisation_url,  # type: ignore[union-attr]
                ),
                pat=pat,
            )
        super().perform_update(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.updated",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_destroy(self, instance: AzureDevOpsConfiguration) -> None:
        log = self._log_for(instance)
        super().perform_destroy(instance)
        log.info("configuration.deleted")
```

(Notes on the implementation:
- `_validate_pat_against_ado` lives at module level so tests can patch it if they want to. It re-raises only on `AzureDevOpsAuthError`; other failures propagate so the caller can decide.
- On update, validation only runs if `personal_access_token` is in `validated_data` — the Task 7 serializer override pops the placeholder, so the placeholder case is automatically skipped.
- `from None` suppresses the inner traceback in the user-facing 400 response.)

- [ ] **Step 5: Run the test file**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_configuration.py -v'
```

Expected: every test in the file passes — including the two new tests and the three existing ones with their new `@responses.activate` decorators.

- [ ] **Step 6: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 7: Run lint**

```bash
make lint
```

Expected: clean.

- [ ] **Step 8: Commit**

```bash
git add api/integrations/azure_devops/views/configuration.py api/tests/unit/integrations/azure_devops/test_configuration.py
git commit -m "$(cat <<'EOF'
feat(integrations): validate PAT against ADO on create/update

The configuration viewset now probes ADO with list_projects(top=1) when
the PAT is being set. On 401/403 ADO replies, the viewset returns 400
with a clear message and does not persist. On update, validation only
runs when the request actually changes the PAT (the serializer override
from the previous commit drops placeholder values).

Network and 5xx failures still propagate so transient unavailability is
not silently ignored. The existing tests are updated to mock the ADO
probe via the responses library; two new tests exercise the
invalid-PAT and placeholder-on-update paths.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Full-suite verification

- [ ] **Step 1: Lint**

From `api/`:

```bash
make lint
```

Expected: clean. If any auto-fixes apply, accept them and either amend the originating commit or add a `style:` follow-up — match what was done in PRs 1 and 2.

- [ ] **Step 2: Type check**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 3: Run the whole new test directory**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/ -v'
```

Expected: every test passes. Approximate count: 23 (PR 2 baseline) + ~2 constants + ~4 exceptions + ~2 types + ~7 client + ~4 PR URL parse + ~4 work-item URL parse + 3 model save + 2 serializer placeholder + 2 viewset (invalid PAT + placeholder skip) = around 50.

- [ ] **Step 4: Regression guard**

```bash
make test opts='tests/unit/integrations/gitlab tests/unit/integrations/github tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/features/test_migrations.py'
```

Expected: all pass.

- [ ] **Step 5: Migration consistency**

```bash
make django-make-migrations opts='--check --dry-run'
```

Expected: `No changes detected` for every app. PR 3 introduces no schema changes.

- [ ] **Step 6: Branch state**

```bash
git status
git log --oneline feat/azure-devops-02-models..HEAD
```

Expected: working tree clean; eight feature commits on this branch ahead of `feat/azure-devops-02-models` (Task 1 through Task 8 each produce one commit; the plan-doc commit is optional and may already exist from a prior step).

---

## Done condition

- Branch `feat/azure-devops-03-client` carries the PR 3 plan doc commit + eight feature commits (plus any optional `style:` follow-ups).
- The Azure DevOps REST client surface for v1 (`list_projects` plus the HTTP plumbing) is live with typed exceptions.
- URL parsing for PR and work-item URLs covers cloud and on-prem shapes; parsing never raises.
- `organisation_url` is normalised on save (trailing slash stripped).
- The serializer drops `personal_access_token == WRITE_ONLY_PLACEHOLDER` from update payloads.
- The configuration viewset validates the PAT against ADO on create, and on update when the PAT actually changes; auth failures surface as 400.
- All new tests pass; mypy strict, ruff, and `flagsmith-lint-tests` are clean. No schema drift.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-02-models`. The next plan in the stack will be written after this PR lands; the spec's section ordering points toward `services/tagging.py` and tag-system-tag constants next.
