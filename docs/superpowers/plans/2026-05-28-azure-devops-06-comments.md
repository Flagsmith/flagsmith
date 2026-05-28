# Azure DevOps Integration — PR 6: Comments service + templates + tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Flagsmith → ADO comment-posting layer: client functions for ADO's PR-thread and work-item-comment endpoints, four markdown templates rendering the linked/unlinked/state-changed/feature-deleted bodies, a `services/comments.py` module exposing four public functions plus a per-feature-state dispatcher helper, and the async task wrappers the future dispatcher PR will invoke.

**Architecture:** Mirror GitLab's `services/comments.py` shape closely. Each public function loads the project's `AzureDevOpsConfiguration`, parses the resource URL via the PR 3 URL parsers, renders the corresponding template with feature/environment context, and POSTs through the client. Failures (`requests.RequestException`) are caught and logged as `comment.post_failed` so the triggering user-facing action still succeeds.

ADO comment endpoints used:
- **Pull requests:** `POST {org}/{project}/_apis/git/pullrequests/{prId}/threads` — body `{"comments": [{"content": "<markdown>"}], "status": 1}` creates a single-comment thread. The project-scoped form avoids needing the repository GUID.
- **Work items:** `POST {org}/{project}/_apis/wit/workItems/{id}/comments` — body `{"text": "<markdown>"}` adds a comment (newer Comments API; `?api-version=7.1-preview.3` is the documented version but `7.1` works for both modern Cloud and recent on-prem releases).

**Tech Stack:** Python 3.12, Django 5.x, Django templates (autoescape disabled per GitLab precedent), `requests`, `task_processor`, `responses` (tests), pytest, mypy strict.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Components → `services/comments.py`", "Data flow → State-change flow (Flagsmith → ADO)", "Data flow → Feature deletion", "Error handling".

**Plan reference (parent):** `docs/superpowers/plans/2026-05-28-azure-devops-05-browse.md`.

**Stack position:** PR 6 of N. Branches off `feat/azure-devops-05-browse`. Branch name: `feat/azure-devops-06-comments`.

---

## Scope deliberately out of PR 6

- The `vcs/services.py` dispatcher wiring that calls `apply_initial_tag` and queues `post_azure_devops_linked_comment.delay(...)` on `FeatureExternalResource` lifecycle events — lands in a later PR.
- The `FeatureState` save-hook call site that invokes `post_state_change_comment_for_feature_state` — the helper lands here so it can be called, but the wiring lands when the dispatcher PR ships.
- The `Feature` soft-delete hook that fans `post_feature_deleted_comment` out across linked resources — same story; the function is callable, the caller wiring is later.

---

## File Structure

- **Modify:** `api/integrations/azure_devops/client/types.py` — no new types in PR 6 (the comment endpoints return shapes we discard).
- **Modify:** `api/integrations/azure_devops/client/api.py` — add `add_pull_request_comment` and `add_work_item_comment`.
- **Modify:** `api/integrations/azure_devops/client/__init__.py` — re-export the two new functions.
- **Create:** `api/integrations/azure_devops/templates/azure_devops/feature_linked_comment.md`
- **Create:** `api/integrations/azure_devops/templates/azure_devops/feature_unlinked_comment.md`
- **Create:** `api/integrations/azure_devops/templates/azure_devops/feature_state_changed_comment.md`
- **Create:** `api/integrations/azure_devops/templates/azure_devops/feature_deleted_comment.md`
- **Modify:** `api/integrations/azure_devops/types.py` — add `AzureDevOpsEnvironmentState` TypedDict (used in template rendering).
- **Create:** `api/integrations/azure_devops/services/comments.py` — five functions: `post_linked_comment`, `post_unlinked_comment`, `post_state_change_comment`, `post_feature_deleted_comment`, `post_state_change_comment_for_feature_state`.
- **Create:** `api/integrations/azure_devops/tasks.py` — four `@register_task_handler()` decorated wrappers.
- **Create:** `api/tests/unit/integrations/azure_devops/test_comments.py` — covers the service functions.
- **Create:** `api/tests/unit/integrations/azure_devops/test_tasks.py` — covers the task wrappers (thin tests that verify the right service function is called).

No other files are touched in this PR.

---

## Pre-flight

- [ ] **Step 0: Confirm working branch**

```bash
cd /Users/asaphkotzin/Dev/flagsmith
git status
git log --oneline -3
```

Expected: branch `feat/azure-devops-06-comments`, HEAD at PR 5's tip (`bed431a51`). Working tree clean.

---

## Task 1: Client comment-posting functions

**Files:**
- Modify: `api/integrations/azure_devops/client/api.py`
- Modify: `api/integrations/azure_devops/client/__init__.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py`

- [ ] **Step 1: Append the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
@responses.activate
def test_add_pull_request_comment__valid_call__posts_thread_with_comment() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/threads",
        json={"id": 1},
        match=[
            responses.matchers.json_params_matcher(
                {
                    "comments": [{"content": "Hello"}],
                    "status": 1,
                }
            ),
        ],
    )

    # When
    add_pull_request_comment(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        pull_request_id=42,
        body="Hello",
    )

    # Then — call landed; matcher already asserts body
    assert len(responses.calls) == 1


@responses.activate
def test_add_pull_request_comment__500_response__raises_http_error() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/threads",
        json={},
        status=500,
    )

    # When
    def call_post() -> None:
        add_pull_request_comment(
            organisation_url=ORG_URL,
            pat=PAT,
            project="proj",
            pull_request_id=42,
            body="x",
        )

    # Then
    with pytest.raises(requests.HTTPError):
        call_post()


@responses.activate
def test_add_work_item_comment__valid_call__posts_comment_text() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/wit/workItems/100/comments",
        json={"id": 1},
        match=[
            responses.matchers.json_params_matcher({"text": "Hello world"}),
        ],
    )

    # When
    add_work_item_comment(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        body="Hello world",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_add_work_item_comment__500_response__raises_http_error() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/wit/workItems/100/comments",
        json={},
        status=500,
    )

    # When
    def call_post() -> None:
        add_work_item_comment(
            organisation_url=ORG_URL,
            pat=PAT,
            project="proj",
            work_item_id=100,
            body="x",
        )

    # Then
    with pytest.raises(requests.HTTPError):
        call_post()
```

Extend the test file's `from integrations.azure_devops.client import ...` block to add `add_pull_request_comment` and `add_work_item_comment`.

- [ ] **Step 2: Run to verify failure**

From `api/`:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -k add_ -v'
```

Expected: ImportError on the two new functions.

- [ ] **Step 3: Add the client functions**

Append to `api/integrations/azure_devops/client/api.py`:

```python
def add_pull_request_comment(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    pull_request_id: int,
    body: str,
) -> None:
    """Post a single-comment thread on an Azure DevOps pull request via
    its project-scoped threads endpoint.

    `project` is the ADO project name from the resource URL; the
    project-scoped form sidesteps needing the repository GUID. `status: 1`
    is the ADO enum value for "Active".
    """
    _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{project}/_apis/git/pullrequests/{pull_request_id}/threads",
        json_body={
            "comments": [{"content": body}],
            "status": 1,
        },
    )


def add_work_item_comment(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    work_item_id: int,
    body: str,
) -> None:
    """Post a comment on an Azure DevOps work item via the modern Comments
    API.
    """
    _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{project}/_apis/wit/workItems/{work_item_id}/comments",
        json_body={"text": body},
    )
```

- [ ] **Step 4: Re-export from `client/__init__.py`**

Add both functions to the existing `from integrations.azure_devops.client.api import ...` block and the `__all__` list. Final `__all__`:

```python
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
    "add_pull_request_comment",
    "add_work_item_comment",
    "list_projects",
    "list_pull_requests",
    "list_repositories",
    "list_work_items",
]
```

- [ ] **Step 5: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
make typecheck
make lint
```

Expected: all clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/client/api.py api/integrations/azure_devops/client/__init__.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add comment-posting functions to the ADO client

add_pull_request_comment posts a single-comment thread (status:1
Active) on the project-scoped PR threads endpoint, avoiding the
need for the repository GUID.

add_work_item_comment uses the modern /_apis/wit/workItems/{id}/comments
endpoint with a JSON body of {"text": "..."}.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Comment templates

**Files:**
- Create: `api/integrations/azure_devops/templates/azure_devops/feature_linked_comment.md`
- Create: `api/integrations/azure_devops/templates/azure_devops/feature_unlinked_comment.md`
- Create: `api/integrations/azure_devops/templates/azure_devops/feature_state_changed_comment.md`
- Create: `api/integrations/azure_devops/templates/azure_devops/feature_deleted_comment.md`

No tests for this task — the templates get exercised by the service-layer tests in Tasks 3-5.

- [ ] **Step 1: Create the linked-comment template**

Create `api/integrations/azure_devops/templates/azure_devops/feature_linked_comment.md` with the following exact contents:

```
{% autoescape off %}🔗 Linked to Flagsmith feature flag `{{ feature_name }}`

| Environment | Enabled | Value |
| :--- | :----- | :------ |
{% for env in environment_states %}| [{{ env.name }}]({{ env.url }}) | {% if env.enabled %}✅ Enabled{% else %}❌ Disabled{% endif %} | {% if env.value is not None %}`{{ env.value }}`{% endif %} |
{% endfor %}
Segment and identity overrides may apply — check each environment above for details.{% endautoescape %}
```

The ADO markdown renderer supports plain Unicode emojis natively; GitLab's `:white_check_mark:` shortcodes aren't supported in ADO PR threads / work-item comments, so we substitute with the literal Unicode characters.

- [ ] **Step 2: Create the unlinked-comment template**

Create `api/integrations/azure_devops/templates/azure_devops/feature_unlinked_comment.md` with the following exact contents:

```
{% autoescape off %}🔓 Unlinked from Flagsmith feature flag `{{ feature_name }}`{% endautoescape %}
```

- [ ] **Step 3: Create the state-changed template**

Create `api/integrations/azure_devops/templates/azure_devops/feature_state_changed_comment.md` with the following exact contents:

```
{% autoescape off %}Feature flag `{{ feature_name }}` in **{{ environment_name }}**{% if scope == "segment" %} for segment **{{ scope_name }}**{% elif scope == "identity" %} for identity **{{ scope_name }}**{% endif %}: {% if enabled %}✅ Enabled{% else %}❌ Disabled{% endif %}{% if value is not None %}, value `{{ value }}`{% endif %}{% endautoescape %}
```

- [ ] **Step 4: Create the deleted-comment template**

Create `api/integrations/azure_devops/templates/azure_devops/feature_deleted_comment.md` with the following exact contents:

```
{% autoescape off %}Feature flag `{{ feature_name }}` was deleted{% endautoescape %}
```

- [ ] **Step 5: Commit**

```bash
git add api/integrations/azure_devops/templates/
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps comment templates

Four markdown templates mirroring GitLab's set: feature_linked,
feature_unlinked, feature_state_changed, feature_deleted. Uses plain
Unicode emojis instead of GitLab-style :white_check_mark: shortcodes
because ADO's markdown renderer doesn't support shortcodes.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Environment-state type + fixture cleanup + service skeleton + `post_linked_comment`

**Files:**
- Modify: `api/integrations/azure_devops/types.py` (append `AzureDevOpsEnvironmentState`)
- Modify: `api/tests/unit/integrations/azure_devops/conftest.py` (give PR fixtures numeric IDs so URLs parse)
- Create: `api/integrations/azure_devops/services/comments.py`
- Create: `api/tests/unit/integrations/azure_devops/test_comments.py`

- [ ] **Step 0: Fix conftest PR-resource fixtures to use numeric IDs**

The PR 4 conftest fixture currently builds URLs like `pullrequest/active` using the resource `state` as the ID, which works for tagging tests (those read `metadata.state`, not the URL) but does **not** parse through `parse_pull_request_url` (the regex requires `\d+`). All comment tests below depend on the URL parsing, so update the helper to take a numeric `pr_id` instead.

The current `_make_pr_resource` in `api/tests/unit/integrations/azure_devops/conftest.py`:

```python
def _make_pr_resource(
    feature: Feature, *, state: str, is_draft: bool = False
) -> FeatureExternalResource:
    metadata = (
        '{"state": "' + state + '", "is_draft": ' + ("true" if is_draft else "false") + "}"
    )
    draft_suffix = "-draft" if is_draft else ""
    return FeatureExternalResource.objects.create(
        feature=feature,
        url=f"https://dev.azure.com/test-org/proj/_git/repo/pullrequest/{state}{draft_suffix}",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata=metadata,
    )
```

Replace with the version that takes an explicit `pr_id`:

```python
def _make_pr_resource(
    feature: Feature, *, pr_id: int, state: str, is_draft: bool = False
) -> FeatureExternalResource:
    metadata = (
        '{"state": "' + state + '", "is_draft": ' + ("true" if is_draft else "false") + "}"
    )
    return FeatureExternalResource.objects.create(
        feature=feature,
        url=f"https://dev.azure.com/test-org/proj/_git/repo/pullrequest/{pr_id}",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata=metadata,
    )
```

Then update the three fixtures that call this helper to pass distinct numeric `pr_id`s. Replace:

```python
@pytest.fixture()
def azure_devops_pr_resource_open(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, state="active", is_draft=False)


@pytest.fixture()
def azure_devops_pr_resource_draft(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, state="active", is_draft=True)


@pytest.fixture()
def azure_devops_pr_resource_merged(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, state="completed")
```

with:

```python
@pytest.fixture()
def azure_devops_pr_resource_open(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, pr_id=1, state="active", is_draft=False)


@pytest.fixture()
def azure_devops_pr_resource_draft(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, pr_id=2, state="active", is_draft=True)


@pytest.fixture()
def azure_devops_pr_resource_merged(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, pr_id=3, state="completed")
```

Verify the PR 4 tagging tests still pass after the fixture change:

```bash
cd api && make test opts='-n0 tests/unit/integrations/azure_devops/test_tagging.py tests/unit/integrations/azure_devops/test_mappers.py -v'
```

Expected: all tagging + mapper tests still pass (they read `metadata.state`, not the URL).

- [ ] **Step 1: Add `AzureDevOpsEnvironmentState` to `types.py`**

The current `api/integrations/azure_devops/types.py` (from PR 4) contains only `AzureDevOpsResourceMetadata`. Replace with:

```python
from typing_extensions import TypedDict


class AzureDevOpsResourceMetadata(TypedDict, total=False):
    """Client-supplied snapshot persisted on ``FeatureExternalResource.metadata``
    when linking an Azure DevOps pull request or work item. Sent by the
    frontend as part of the link request; the backend stores it verbatim
    as a JSON string.

    Fields are typed for both PR and work-item resources; not every field
    applies to both — ``state`` is universal, ``is_draft`` is PR-only,
    ``work_item_type`` is work-item-only, ``title`` is universal.
    """

    title: str
    state: str
    work_item_type: str
    is_draft: bool


class AzureDevOpsEnvironmentState(TypedDict):
    """Per-environment feature-state row included in linked / state-change
    comment templates. The mapping mirrors GitLab's GitLabEnvironmentState.
    """

    name: str
    url: str
    enabled: bool
    value: str | int | bool | None
```

- [ ] **Step 2: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_comments.py` with:

```python
import pytest
import responses

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.comments import post_linked_comment

ORG_URL = "https://dev.azure.com/test-org"


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__pr_resource__posts_thread(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    environment: object,  # noqa: ARG001 - existence triggers env state in template
) -> None:
    # Given
    expected_url = f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads"
    responses.post(expected_url, json={"id": 1})

    # When
    post_linked_comment(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1
    body = responses.calls[0].request.body
    assert body is not None
    body_text = body.decode() if isinstance(body, bytes) else body
    assert "Linked to Flagsmith feature flag" in body_text


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__work_item_resource__posts_comment(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_work_item_resource_open: FeatureExternalResource,
    environment: object,  # noqa: ARG001
) -> None:
    # Given — work-item URL from the conftest fixture is
    # "https://dev.azure.com/test-org/proj/_workitems/edit/<hash%10000>"
    # so the work_item_id varies; the regex captures the integer.
    import re

    match = re.search(
        r"_workitems/edit/(\d+)",
        azure_devops_work_item_resource_open.url,
    )
    assert match is not None
    work_item_id = int(match.group(1))

    expected_url = (
        f"{ORG_URL}/proj/_apis/wit/workItems/{work_item_id}/comments"
    )
    responses.post(expected_url, json={"id": 1})

    # When
    post_linked_comment(azure_devops_work_item_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__no_configuration__noop(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — no AzureDevOpsConfiguration exists

    # When
    post_linked_comment(azure_devops_pr_resource_open)

    # Then — no outbound call was made
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__ado_500__logs_and_returns(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    expected_url = f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads"
    responses.post(expected_url, json={}, status=500)

    # When — must not raise
    post_linked_comment(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_post_linked_comment__unparseable_url__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    from features.feature_external_resources.models import (
        FeatureExternalResource,
        ResourceType,
    )

    bogus = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://example.com/not/an/ado/url",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata='{"state": "active", "is_draft": false}',
    )

    # When
    post_linked_comment(bogus)

    # Then — URL parsing returns None; no call attempted
    assert len(responses.calls) == 0
```

- [ ] **Step 3: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
```

Expected: ImportError on `post_linked_comment`.

- [ ] **Step 4: Create the service module**

Create `api/integrations/azure_devops/services/comments.py` with the following exact contents:

```python
import requests
import structlog
from django.db.models import Q
from django.template.loader import render_to_string

from core.helpers import get_current_site_url
from features.feature_external_resources.models import (
    AZURE_DEVOPS_RESOURCE_TYPES,
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature, FeatureState
from integrations.azure_devops.client import (
    add_pull_request_comment,
    add_work_item_comment,
)
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.url_parsing import (
    parse_pull_request_url,
    parse_work_item_url,
)
from integrations.azure_devops.types import AzureDevOpsEnvironmentState

logger = structlog.get_logger("azure_devops")


def _post_to_resource(
    *,
    config: AzureDevOpsConfiguration,
    resource_url: str,
    resource_type: str,
    feature_id: int,
    body: str,
) -> None:
    """Parse an ADO resource URL and post the comment via the right
    endpoint. Used by every public function in this module.
    """
    if resource_type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
        ref = parse_pull_request_url(resource_url)
        if ref is None:
            return
        log = logger.bind(
            organisation__id=config.project.organisation_id,
            project__id=config.project_id,
            feature__id=feature_id,
            ado__project=ref.project,
            ado__resource__id=ref.pull_request_id,
        )
        try:
            add_pull_request_comment(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=ref.project,
                pull_request_id=ref.pull_request_id,
                body=body,
            )
        except requests.RequestException as exc:
            log.warning("comment.post_failed", exc_info=exc)
            return
        log.info("comment.posted")
        return

    if resource_type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
        work_ref = parse_work_item_url(resource_url)
        if work_ref is None:
            return
        log = logger.bind(
            organisation__id=config.project.organisation_id,
            project__id=config.project_id,
            feature__id=feature_id,
            ado__project=work_ref.project,
            ado__resource__id=work_ref.work_item_id,
        )
        try:
            add_work_item_comment(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=work_ref.project,
                work_item_id=work_ref.work_item_id,
                body=body,
            )
        except requests.RequestException as exc:
            log.warning("comment.post_failed", exc_info=exc)
            return
        log.info("comment.posted")


def _get_environment_states(feature: Feature) -> list[AzureDevOpsEnvironmentState]:
    """Gather the current enabled state and value for ``feature`` across all
    environments in its project, suitable for rendering in a comment.
    """
    from environments.models import Environment

    site_url = get_current_site_url()
    environments = Environment.objects.filter(
        project=feature.project,
    ).order_by("id")

    states: list[AzureDevOpsEnvironmentState] = []
    for environment in environments:
        feature_state: FeatureState | None = (
            FeatureState.objects.get_live_feature_states(
                environment=environment,
                additional_filters=Q(
                    feature=feature,
                    identity__isnull=True,
                    feature_segment__isnull=True,
                ),
            ).first()
        )
        if feature_state is None:
            continue  # pragma: no cover — initial states are always created

        value = feature_state.get_feature_state_value()
        env_url = (
            f"{site_url}/project/{feature.project_id}"
            f"/environment/{environment.api_key}"
            f"/features?feature={feature.id}"
        )
        states.append(
            {
                "name": environment.name,
                "url": env_url,
                "enabled": feature_state.enabled,
                "value": value if value not in (None, "") else None,
            }
        )
    return states


def post_linked_comment(resource: FeatureExternalResource) -> None:
    """Post a comment on the linked ADO PR or work item showing the
    feature flag's current state across all environments. No-op when the
    project has no AzureDevOpsConfiguration.
    """
    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project=resource.feature.project,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    feature = resource.feature
    environment_states = _get_environment_states(feature)
    body = render_to_string(
        "azure_devops/feature_linked_comment.md",
        {
            "feature_name": feature.name,
            "environment_states": environment_states,
        },
    )

    _post_to_resource(
        config=config,
        resource_url=resource.url,
        resource_type=resource.type,
        feature_id=feature.id,
        body=body,
    )
```

- [ ] **Step 5: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
make typecheck
make lint
```

Expected: 5 passed; mypy + lint clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/types.py api/integrations/azure_devops/services/comments.py api/tests/unit/integrations/azure_devops/test_comments.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps post_linked_comment service

Loads the project's AzureDevOpsConfiguration, gathers per-environment
state, renders the linked-comment template, and dispatches to the
right ADO endpoint based on resource type via _post_to_resource. PR
URLs go to /pullrequests/{id}/threads; work-item URLs go to
/workItems/{id}/comments.

Failures (requests.RequestException) are caught and logged as
"comment.post_failed" so the triggering link action still succeeds.
Successes log "comment.posted". No-op when the configuration is
absent or the URL can't be parsed.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: `post_unlinked_comment` + `post_feature_deleted_comment`

**Files:**
- Modify: `api/integrations/azure_devops/services/comments.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_comments.py`

These two share the same pattern: load config, render a simple template, fan out to one or more linked resources. `post_unlinked_comment` takes the resource fields directly (because the row is gone by the time the async task runs). `post_feature_deleted_comment` fans across every linked resource for a feature.

- [ ] **Step 1: Append the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_comments.py`:

```python
from integrations.azure_devops.services.comments import (
    post_feature_deleted_comment,
    post_unlinked_comment,
)


@pytest.mark.django_db
@responses.activate
def test_post_unlinked_comment__pr_resource__posts_thread(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    expected_url = f"{ORG_URL}/proj/_apis/git/pullrequests/77/threads"
    responses.post(expected_url, json={"id": 1})

    # When
    post_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 1
    body = responses.calls[0].request.body
    assert body is not None
    body_text = body.decode() if isinstance(body, bytes) else body
    assert "Unlinked from Flagsmith" in body_text


@pytest.mark.django_db
@responses.activate
def test_post_unlinked_comment__no_configuration__noop(
    feature: Feature,
) -> None:
    # Given — no AzureDevOpsConfiguration exists

    # When
    post_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__multiple_linked_resources__posts_to_each(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_work_item_resource_open: FeatureExternalResource,
    feature: Feature,
) -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads",
        json={"id": 1},
    )
    import re

    match = re.search(
        r"_workitems/edit/(\d+)",
        azure_devops_work_item_resource_open.url,
    )
    assert match is not None
    work_item_id = int(match.group(1))
    responses.post(
        f"{ORG_URL}/proj/_apis/wit/workItems/{work_item_id}/comments",
        json={"id": 1},
    )

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 2


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__no_linked_resources__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given — no FeatureExternalResource rows of AZURE_DEVOPS_* type

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_feature_deleted_comment__no_configuration__noop(
    feature: Feature,
) -> None:
    # Given — no AzureDevOpsConfiguration exists

    # When
    post_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    assert len(responses.calls) == 0
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
```

Expected: ImportErrors on the two new symbols.

- [ ] **Step 3: Append the two service functions**

Append to `api/integrations/azure_devops/services/comments.py`:

```python
def post_unlinked_comment(
    feature_name: str,
    feature_id: int,
    resource_url: str,
    resource_type: str,
    project_id: int,
) -> None:
    """Post a comment on the ADO resource informing that the feature flag
    has been unlinked.

    All parameters are passed explicitly because the
    ``FeatureExternalResource`` row no longer exists by the time this
    runs asynchronously.
    """
    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project_id=project_id,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    body = render_to_string(
        "azure_devops/feature_unlinked_comment.md",
        {"feature_name": feature_name},
    )

    _post_to_resource(
        config=config,
        resource_url=resource_url,
        resource_type=resource_type,
        feature_id=feature_id,
        body=body,
    )


def post_feature_deleted_comment(
    feature_name: str,
    feature_id: int,
    project_id: int,
) -> None:
    """Post a comment on every linked Azure DevOps resource informing that
    the feature flag has been deleted.

    All parameters are passed explicitly because the feature is being
    soft-deleted and may no longer be fully usable as an ORM object by
    the time this runs asynchronously.
    """
    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project_id=project_id,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    resources = FeatureExternalResource.objects.filter(
        feature_id=feature_id,
        type__in=AZURE_DEVOPS_RESOURCE_TYPES,
    )
    if not resources.exists():
        return

    body = render_to_string(
        "azure_devops/feature_deleted_comment.md",
        {"feature_name": feature_name},
    )

    for resource in resources:
        _post_to_resource(
            config=config,
            resource_url=resource.url,
            resource_type=resource.type,
            feature_id=feature_id,
            body=body,
        )
```

- [ ] **Step 4: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
make typecheck
make lint
```

Expected: 10 passed; mypy + lint clean.

- [ ] **Step 5: Commit**

```bash
git add api/integrations/azure_devops/services/comments.py api/tests/unit/integrations/azure_devops/test_comments.py
git commit -m "$(cat <<'EOF'
feat(integrations): add post_unlinked_comment and post_feature_deleted_comment

post_unlinked_comment renders the unlinked template and dispatches to
the right ADO endpoint. Takes resource fields explicitly because the
FER row is gone by the time this runs.

post_feature_deleted_comment loads every linked AZURE_DEVOPS_* resource
for the feature and posts the deletion notice to each one.

Both no-op when the project has no AzureDevOpsConfiguration.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: `post_state_change_comment` + the for-feature-state dispatcher helper

**Files:**
- Modify: `api/integrations/azure_devops/services/comments.py`
- Modify: `api/integrations/azure_devops/tasks.py` (created in Task 6, but the helper in this task references it via deferred import)
- Modify: `api/tests/unit/integrations/azure_devops/test_comments.py`

`post_state_change_comment(feature_state)` renders the state-change template with environment + scope context and fans out to every linked ADO resource on the feature. `post_state_change_comment_for_feature_state(feature_state)` is the entry point called from the `FeatureState` save hook — it short-circuits when the project has no `azure_devops_config` and otherwise queues `post_state_change_comment.delay(feature_state.id)`. Since `tasks.py` doesn't exist yet, we use a deferred import inside the helper (as GitLab does).

- [ ] **Step 1: Append the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_comments.py`:

```python
from integrations.azure_devops.services.comments import (
    post_state_change_comment,
    post_state_change_comment_for_feature_state,
)


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__environment_scope__posts_to_each_resource(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    feature: Feature,
    environment: object,  # noqa: ARG001
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=feature.project.environments.first(),
    ).filter(feature=feature, identity__isnull=True, feature_segment__isnull=True).first()
    assert feature_state is not None
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/threads",
        json={"id": 1},
    )

    # When
    post_state_change_comment(feature_state)

    # Then
    assert len(responses.calls) == 1
    body = responses.calls[0].request.body
    assert body is not None
    body_text = body.decode() if isinstance(body, bytes) else body
    assert feature.name in body_text


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__no_resources_linked__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
    environment: object,  # noqa: ARG001
) -> None:
    # Given — no FeatureExternalResource rows
    from features.models import FeatureState

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=feature.project.environments.first(),
    ).filter(feature=feature, identity__isnull=True, feature_segment__isnull=True).first()
    assert feature_state is not None

    # When
    post_state_change_comment(feature_state)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_post_state_change_comment__no_configuration__noop(
    azure_devops_pr_resource_open: FeatureExternalResource,
    feature: Feature,
    environment: object,  # noqa: ARG001
) -> None:
    # Given — no AzureDevOpsConfiguration
    from features.models import FeatureState

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=feature.project.environments.first(),
    ).filter(feature=feature, identity__isnull=True, feature_segment__isnull=True).first()
    assert feature_state is not None

    # When
    post_state_change_comment(feature_state)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
def test_post_state_change_comment_for_feature_state__with_config__queues_task(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
    environment: object,  # noqa: ARG001
    mocker: object,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=feature.project.environments.first(),
    ).filter(feature=feature, identity__isnull=True, feature_segment__isnull=True).first()
    assert feature_state is not None
    delay_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_azure_devops_state_change_comment.delay"
    )

    # When
    post_state_change_comment_for_feature_state(feature_state)

    # Then
    delay_mock.assert_called_once()
    args, kwargs = delay_mock.call_args
    assert kwargs.get("args") == (feature_state.id,) or args == ((feature_state.id,),)


@pytest.mark.django_db
def test_post_state_change_comment_for_feature_state__no_config__skips_dispatch(
    feature: Feature,
    environment: object,  # noqa: ARG001
    mocker: object,
) -> None:
    # Given — no AzureDevOpsConfiguration
    from features.models import FeatureState

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=feature.project.environments.first(),
    ).filter(feature=feature, identity__isnull=True, feature_segment__isnull=True).first()
    assert feature_state is not None
    delay_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_azure_devops_state_change_comment.delay"
    )

    # When
    post_state_change_comment_for_feature_state(feature_state)

    # Then
    delay_mock.assert_not_called()
```

The `mocker` fixture comes from `pytest-mock`, which is already a project dev dep (used widely in the test suite).

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
```

Expected: ImportErrors on the two new symbols.

- [ ] **Step 3: Append the two service functions**

Append to `api/integrations/azure_devops/services/comments.py`:

```python
def post_state_change_comment_for_feature_state(
    feature_state: FeatureState,
) -> None:
    """Dispatch a state-change comment task for ``feature_state`` when the
    project has an Azure DevOps integration configured. No-op otherwise
    so projects without ADO don't pay for a queue entry and a
    ``AzureDevOpsConfiguration`` lookup per feature-state save.
    """
    from integrations.azure_devops.tasks import (
        post_azure_devops_state_change_comment,
    )

    if not feature_state.environment:
        return
    if not hasattr(feature_state.environment.project, "azure_devops_config"):
        return
    post_azure_devops_state_change_comment.delay(args=(feature_state.id,))


def post_state_change_comment(feature_state: FeatureState) -> None:
    """Post a comment on every linked ADO resource when a feature flag's
    state changes, covering environment-level, segment override, and
    identity override scopes.
    """
    feature = feature_state.feature

    try:
        config: AzureDevOpsConfiguration = AzureDevOpsConfiguration.objects.get(
            project=feature.project,
        )
    except AzureDevOpsConfiguration.DoesNotExist:
        return

    resources = feature.external_resources.filter(type__in=AZURE_DEVOPS_RESOURCE_TYPES)
    if not resources.exists():
        return

    environment = feature_state.environment
    if environment is None:
        return

    if feature_state.feature_segment_id is not None:
        feature_segment = feature_state.feature_segment
        scope = "segment"
        scope_name: str | None = (
            feature_segment.segment.name if feature_segment else None
        )
    elif feature_state.identity_id is not None:
        identity = feature_state.identity
        scope = "identity"
        scope_name = identity.identifier if identity else None
    else:
        scope = "environment"
        scope_name = None

    value = feature_state.get_feature_state_value()
    body = render_to_string(
        "azure_devops/feature_state_changed_comment.md",
        {
            "feature_name": feature.name,
            "environment_name": environment.name,
            "enabled": feature_state.enabled,
            "value": value if value not in (None, "") else None,
            "scope": scope,
            "scope_name": scope_name,
        },
    )

    for resource in resources:
        _post_to_resource(
            config=config,
            resource_url=resource.url,
            resource_type=resource.type,
            feature_id=feature.id,
            body=body,
        )
```

- [ ] **Step 4: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
make typecheck
make lint
```

Expected: 15 passed; mypy + lint clean. The `for_feature_state` tests use `mocker` to mock the task that lands in Task 6, so they pass even though `tasks.py` doesn't exist yet — the deferred import is evaluated at call time, and `mocker.patch` patches the import target.

If `mocker.patch` fails because the target module doesn't exist yet, those two tests will be skipped until Task 6 lands. Run only the ones that don't depend on `tasks.py` in this step:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v -k "not for_feature_state"'
```

Then verify the for-feature-state tests pass after Task 6.

- [ ] **Step 5: Commit**

```bash
git add api/integrations/azure_devops/services/comments.py api/tests/unit/integrations/azure_devops/test_comments.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps state-change comment service

post_state_change_comment fans the state-changed template out to every
linked ADO resource on the feature, with scope (environment/segment/
identity) and value baked into the rendered body.

post_state_change_comment_for_feature_state is the entry point the
FeatureState save hook will invoke in a later PR — it short-circuits
when the project has no azure_devops_config (cheap hasattr check) and
otherwise queues the task. The task itself lands in the next commit.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Async task wrappers

**Files:**
- Create: `api/integrations/azure_devops/tasks.py`
- Create: `api/tests/unit/integrations/azure_devops/test_tasks.py`

Four `@register_task_handler()` decorated wrappers around the comment service functions. Each task loads the relevant FER (or, for unlinked / deleted, takes the fields directly) and forwards to the service.

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_tasks.py` with the following exact contents:

```python
import pytest

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.azure_devops.tasks import (
    post_azure_devops_feature_deleted_comment,
    post_azure_devops_linked_comment,
    post_azure_devops_state_change_comment,
    post_azure_devops_unlinked_comment,
)


@pytest.mark.django_db
def test_post_linked_task__valid_id__forwards_to_service(
    azure_devops_pr_resource_open: FeatureExternalResource,
    mocker: object,
) -> None:
    # Given
    service_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_linked_comment"
    )

    # When
    post_azure_devops_linked_comment(azure_devops_pr_resource_open.id)

    # Then
    service_mock.assert_called_once_with(azure_devops_pr_resource_open)


@pytest.mark.django_db
def test_post_linked_task__missing_resource__noop(
    mocker: object,
) -> None:
    # Given
    service_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_linked_comment"
    )

    # When
    post_azure_devops_linked_comment(999999)

    # Then
    service_mock.assert_not_called()


@pytest.mark.django_db
def test_post_unlinked_task__valid_args__forwards_to_service(
    feature: Feature,
    mocker: object,
) -> None:
    # Given
    service_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_unlinked_comment"
    )

    # When
    post_azure_devops_unlinked_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        resource_url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1",
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
        project_id=feature.project_id,
    )

    # Then
    service_mock.assert_called_once()


@pytest.mark.django_db
def test_post_state_change_task__valid_id__forwards_to_service(
    feature: Feature,
    environment: object,  # noqa: ARG001
    mocker: object,
) -> None:
    # Given
    from features.models import FeatureState

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=feature.project.environments.first(),
    ).filter(feature=feature, identity__isnull=True, feature_segment__isnull=True).first()
    assert feature_state is not None
    service_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_state_change_comment"
    )

    # When
    post_azure_devops_state_change_comment(feature_state.id)

    # Then
    service_mock.assert_called_once()


@pytest.mark.django_db
def test_post_state_change_task__missing_feature_state__noop(
    mocker: object,
) -> None:
    # Given
    service_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_state_change_comment"
    )

    # When
    post_azure_devops_state_change_comment(999999)

    # Then
    service_mock.assert_not_called()


@pytest.mark.django_db
def test_post_feature_deleted_task__valid_args__forwards_to_service(
    feature: Feature,
    mocker: object,
) -> None:
    # Given
    service_mock = mocker.patch(  # type: ignore[attr-defined]
        "integrations.azure_devops.tasks.post_feature_deleted_comment"
    )

    # When
    post_azure_devops_feature_deleted_comment(
        feature_name=feature.name,
        feature_id=feature.id,
        project_id=feature.project_id,
    )

    # Then
    service_mock.assert_called_once()
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_tasks.py -v'
```

Expected: ImportError on the four task names.

- [ ] **Step 3: Create the tasks module**

Create `api/integrations/azure_devops/tasks.py` with the following exact contents:

```python
import structlog
from task_processor.decorators import register_task_handler

from features.feature_external_resources.models import FeatureExternalResource
from features.models import FeatureState
from integrations.azure_devops.services.comments import (
    post_feature_deleted_comment,
    post_linked_comment,
    post_state_change_comment,
    post_unlinked_comment,
)

logger = structlog.get_logger("azure_devops")


@register_task_handler()
def post_azure_devops_linked_comment(resource_id: int) -> None:
    """Post a comment on the linked Azure DevOps resource showing the
    feature flag's current state. Dispatched at link time.
    """
    try:
        resource = FeatureExternalResource.objects.get(id=resource_id)
    except FeatureExternalResource.DoesNotExist:
        return
    post_linked_comment(resource)


@register_task_handler()
def post_azure_devops_unlinked_comment(
    feature_name: str,
    feature_id: int,
    resource_url: str,
    resource_type: str,
    project_id: int,
) -> None:
    """Post a comment on the ADO resource informing that the feature flag
    has been unlinked. Dispatched at unlink time. All data is passed
    directly because the resource row no longer exists.
    """
    post_unlinked_comment(
        feature_name=feature_name,
        feature_id=feature_id,
        resource_url=resource_url,
        resource_type=resource_type,
        project_id=project_id,
    )


@register_task_handler()
def post_azure_devops_state_change_comment(feature_state_id: int) -> None:
    """Post a comment on every linked Azure DevOps resource when a feature
    flag's state changes. Dispatched from the feature-state save hook.
    """
    try:
        feature_state = FeatureState.objects.select_related(
            "feature",
            "environment",
            "feature_segment__segment",
            "feature__project",
            "identity",
        ).get(id=feature_state_id)
    except FeatureState.DoesNotExist:
        return
    post_state_change_comment(feature_state)


@register_task_handler()
def post_azure_devops_feature_deleted_comment(
    feature_name: str,
    feature_id: int,
    project_id: int,
) -> None:
    """Post a comment on every linked Azure DevOps resource informing that
    the feature flag has been deleted. Dispatched from the Feature
    soft-delete hook.
    """
    post_feature_deleted_comment(
        feature_name=feature_name,
        feature_id=feature_id,
        project_id=project_id,
    )
```

- [ ] **Step 4: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_tasks.py -v'
make typecheck
make lint
```

Expected: 6 passed.

- [ ] **Step 5: Run the for_feature_state tests skipped in Task 5**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_comments.py -v'
```

Expected: 15 passed (the two `for_feature_state` tests now resolve their patch target).

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/tasks.py api/tests/unit/integrations/azure_devops/test_tasks.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps task wrappers

Four @register_task_handler() decorated wrappers that the dispatcher
PR will queue via .delay(): post_azure_devops_linked_comment,
post_azure_devops_unlinked_comment, post_azure_devops_state_change_comment,
post_azure_devops_feature_deleted_comment.

Each task is a thin loader-and-forwarder onto the underlying service
function — the service functions hold the business logic (config lookup,
URL parsing, template rendering, HTTP) and are independently tested.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Full-suite verification

- [ ] **Step 1: Lint, typecheck, ADO tests, regression guard, migrations**

```bash
cd api
make lint
make typecheck
make test opts='-n0 tests/unit/integrations/azure_devops/ -v'
make test opts='tests/unit/integrations/gitlab tests/unit/integrations/github tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/features/test_migrations.py'
make django-make-migrations opts='--check --dry-run'
```

Expected: all clean; ~200 ADO tests pass (PR 5 baseline 173 + 4 client + 15 comments + 6 tasks ≈ 198); regression suite passes; no migration drift.

- [ ] **Step 2: Branch state**

```bash
git status
git log --oneline feat/azure-devops-05-browse..HEAD
```

Expected: working tree clean; 6 feature commits on this branch ahead of `feat/azure-devops-05-browse`, plus a plan-doc commit at the base.

---

## Done condition

- Branch `feat/azure-devops-06-comments` carries the PR 6 plan-doc commit plus six feature commits.
- The Flagsmith → ADO comment-posting layer is callable but not yet invoked from anywhere (dispatcher wiring is a later PR).
- All new tests pass; mypy strict, ruff, `flagsmith-lint-tests` clean.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-05-browse`.
