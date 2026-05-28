# Azure DevOps Integration — PR 7: Labels service + tasks

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Flagsmith → ADO labelling layer: client functions for ADO's PR labels and work-item tags, a `services/labels.py` module, and two task wrappers (apply/remove) the dispatcher PR will invoke. Gated by `AzureDevOpsConfiguration.labeling_enabled`.

**Architecture:** Mirror GitLab's `services/labels.py`. Two ADO-specific quirks:

1. **PR labels** use the project-scoped endpoint `POST {org}/{project}/_apis/git/pullrequests/{prId}/labels` (body `{"name": "flagsmith"}`) — no repository GUID needed. Delete: `DELETE {org}/{project}/_apis/git/pullrequests/{prId}/labels/{name}`. POST on an existing label returns 200 (idempotent); DELETE on a missing label returns 404 (swallowed).

2. **Work-item tags** live in the `System.Tags` field as a semicolon-separated string. ADO has no "add tag" / "remove tag" endpoint — we must GET the work item, parse the field, modify, and PATCH back the full new value. Add: read → split → add `"flagsmith"` (if not present) → join → PATCH. Remove: read → split → filter out `"flagsmith"` → join → PATCH.

**Tech Stack:** Python 3.12, Django, requests, `task_processor`, `responses` (tests), pytest, mypy strict.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Components → `services/labels.py`", "Error handling → Subscription drift" (404/409 handling pattern).

**Stack position:** PR 7 of N. Branches off `feat/azure-devops-06-comments`. Branch name: `feat/azure-devops-07-labels`.

---

## Scope deliberately out of PR 7

- The `vcs/services.py` dispatcher wiring that queues `apply_azure_devops_label.delay(...)` / `remove_azure_devops_label.delay(...)` — lands in a later PR.
- A "flagsmith" label colour / definition push (GitLab needs to create the label first; ADO PR labels and work-item tags don't need pre-registration).

---

## Constants

ADO uses the literal tag string `"flagsmith"` (lowercase, no spaces) for both PR labels and work-item tags. Defined once in `constants.py`.

---

## File Structure

- **Modify:** `api/integrations/azure_devops/constants.py` — add `AZURE_DEVOPS_FLAGSMITH_LABEL = "flagsmith"`.
- **Modify:** `api/integrations/azure_devops/client/api.py` — add four client functions: `add_tag_to_pull_request`, `remove_tag_from_pull_request`, `add_tag_to_work_item`, `remove_tag_from_work_item`. The work-item ones are GET-then-PATCH; the helper `_get_work_item_tags(...)` reads the current tag set.
- **Modify:** `api/integrations/azure_devops/client/__init__.py` — re-export the four new functions.
- **Create:** `api/integrations/azure_devops/services/labels.py` — `apply_flagsmith_label_to_resource(resource)` and `remove_flagsmith_label_from_resource(...)` plus the resource-kind dispatch helper. Mirrors GitLab.
- **Modify:** `api/integrations/azure_devops/tasks.py` — add `apply_azure_devops_label` and `remove_azure_devops_label`.
- **Modify:** `api/tests/unit/integrations/azure_devops/test_client.py` — append tests for the four new client functions.
- **Create:** `api/tests/unit/integrations/azure_devops/test_labels.py` — cover the service functions.
- **Modify:** `api/tests/unit/integrations/azure_devops/test_tasks.py` — append tests for the two new task wrappers.

No other files are touched.

---

## Pre-flight

- [ ] **Step 0: Confirm working branch**

```bash
cd /Users/asaphkotzin/Dev/flagsmith
git status
git log --oneline -3
```

Expected: branch `feat/azure-devops-07-labels`, HEAD at PR 6's tip (`e8ae15bfa`). Working tree clean.

---

## Task 1: PR label client functions

**Files:**
- Modify: `api/integrations/azure_devops/constants.py`
- Modify: `api/integrations/azure_devops/client/api.py`
- Modify: `api/integrations/azure_devops/client/__init__.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py`

- [ ] **Step 1: Add the constant**

In `api/integrations/azure_devops/constants.py`, append:

```python
AZURE_DEVOPS_FLAGSMITH_LABEL = "flagsmith"
```

- [ ] **Step 2: Append the failing PR-label tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
@responses.activate
def test_add_tag_to_pull_request__valid_call__posts_label() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/labels",
        json={"id": "label-1", "name": "flagsmith"},
        match=[
            responses.matchers.json_params_matcher({"name": "flagsmith"}),
        ],
    )

    # When
    add_tag_to_pull_request(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        pull_request_id=42,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_remove_tag_from_pull_request__existing_label__deletes() -> None:
    # Given
    responses.delete(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/labels/flagsmith",
        json={},
        status=204,
    )

    # When
    remove_tag_from_pull_request(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        pull_request_id=42,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_remove_tag_from_pull_request__missing_label__swallows_404() -> None:
    # Given
    responses.delete(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/labels/flagsmith",
        json={},
        status=404,
    )

    # When — must not raise
    remove_tag_from_pull_request(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        pull_request_id=42,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 1
```

Extend the test file's `from integrations.azure_devops.client import (...)` block to include `add_tag_to_pull_request` and `remove_tag_from_pull_request`.

- [ ] **Step 3: Run to verify failure**

From `api/`:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -k tag_to_pull -v'
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -k tag_from_pull -v'
```

Expected: ImportErrors.

- [ ] **Step 4: Add the PR-label client functions**

Append to `api/integrations/azure_devops/client/api.py`:

```python
def add_tag_to_pull_request(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    pull_request_id: int,
    tag: str,
) -> None:
    """Add a label to a pull request. Idempotent on the ADO side — POSTing
    a label that already exists returns 200 with the existing record.
    """
    _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{project}/_apis/git/pullrequests/{pull_request_id}/labels",
        json_body={"name": tag},
    )


def remove_tag_from_pull_request(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    pull_request_id: int,
    tag: str,
) -> None:
    """Delete a label from a pull request. Swallows 404 (label-already-gone
    is the desired terminal state).
    """
    try:
        _ado_request(
            "DELETE",
            organisation_url,
            pat,
            path=f"{project}/_apis/git/pullrequests/{pull_request_id}/labels/{tag}",
        )
    except AzureDevOpsNotFoundError:
        return
```

Add `AzureDevOpsNotFoundError` to the existing imports at the top of `client/api.py` if not already present:

```python
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)
```

- [ ] **Step 5: Re-export from `client/__init__.py`**

Add `add_tag_to_pull_request` and `remove_tag_from_pull_request` to the existing `from integrations.azure_devops.client.api import (...)` block and the `__all__` list (alphabetical).

- [ ] **Step 6: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -v'
make typecheck
make lint
```

Expected: all clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/constants.py api/integrations/azure_devops/client/api.py api/integrations/azure_devops/client/__init__.py api/tests/unit/integrations/azure_devops/test_client.py
git commit -m "$(cat <<'EOF'
feat(integrations): add PR label client functions to the ADO client

add_tag_to_pull_request POSTs to /_apis/git/pullrequests/{id}/labels
(project-scoped form — no repository GUID required). Idempotent on the
ADO side.

remove_tag_from_pull_request DELETEs and swallows 404 (label already
gone is the desired terminal state).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Work-item tag client functions (GET + PATCH)

**Files:**
- Modify: `api/integrations/azure_devops/client/api.py`
- Modify: `api/integrations/azure_devops/client/__init__.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_client.py`

ADO work items store tags as a semicolon-separated `System.Tags` field. To add or remove a tag we GET the current value, modify it, and PATCH the field back. Both add and remove are wrapped so callers stay simple.

- [ ] **Step 1: Append the failing work-item tag tests**

Append to `api/tests/unit/integrations/azure_devops/test_client.py`:

```python
@responses.activate
def test_add_tag_to_work_item__no_existing_tags__patches_with_new_tag() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {}},
        match=[
            responses.matchers.query_param_matcher(
                {"fields": "System.Tags"},
                strict_match=False,
            )
        ],
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "flagsmith"}},
        match=[
            responses.matchers.json_params_matcher(
                [
                    {
                        "op": "add",
                        "path": "/fields/System.Tags",
                        "value": "flagsmith",
                    }
                ]
            ),
        ],
    )

    # When
    add_tag_to_work_item(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 2


@responses.activate
def test_add_tag_to_work_item__tag_already_present__no_patch_call() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "existing; flagsmith"}},
    )

    # When
    add_tag_to_work_item(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        tag="flagsmith",
    )

    # Then — only the GET; no PATCH
    assert len(responses.calls) == 1


@responses.activate
def test_add_tag_to_work_item__existing_other_tags__appends() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "alpha; beta"}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "alpha; beta; flagsmith"}},
        match=[
            responses.matchers.json_params_matcher(
                [
                    {
                        "op": "add",
                        "path": "/fields/System.Tags",
                        "value": "alpha; beta; flagsmith",
                    }
                ]
            ),
        ],
    )

    # When
    add_tag_to_work_item(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 2


@responses.activate
def test_remove_tag_from_work_item__present__patches_with_filtered_tags() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "alpha; flagsmith; beta"}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "alpha; beta"}},
        match=[
            responses.matchers.json_params_matcher(
                [
                    {
                        "op": "add",
                        "path": "/fields/System.Tags",
                        "value": "alpha; beta",
                    }
                ]
            ),
        ],
    )

    # When
    remove_tag_from_work_item(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 2


@responses.activate
def test_remove_tag_from_work_item__absent__no_patch_call() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "alpha; beta"}},
    )

    # When
    remove_tag_from_work_item(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        tag="flagsmith",
    )

    # Then — only the GET; no PATCH
    assert len(responses.calls) == 1


@responses.activate
def test_remove_tag_from_work_item__last_tag__patches_to_empty_string() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": "flagsmith"}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/100",
        json={"id": 100, "fields": {"System.Tags": ""}},
        match=[
            responses.matchers.json_params_matcher(
                [
                    {
                        "op": "add",
                        "path": "/fields/System.Tags",
                        "value": "",
                    }
                ]
            ),
        ],
    )

    # When
    remove_tag_from_work_item(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        tag="flagsmith",
    )

    # Then
    assert len(responses.calls) == 2
```

Extend the imports to include `add_tag_to_work_item` and `remove_tag_from_work_item`.

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_client.py -k work_item -v'
```

Expected: ImportErrors.

- [ ] **Step 3: Add the work-item tag client functions**

Append to `api/integrations/azure_devops/client/api.py`:

```python
def _get_work_item_tags(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    work_item_id: int,
) -> list[str]:
    """Fetch a work item's current System.Tags field, parsed as a list."""
    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path=f"{project}/_apis/wit/workitems/{work_item_id}",
        params={"fields": "System.Tags"},
    )
    payload = response.json()
    raw = payload.get("fields", {}).get("System.Tags", "") or ""
    return [t.strip() for t in raw.split(";") if t.strip()]


def _patch_work_item_tags(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    work_item_id: int,
    tags: list[str],
) -> None:
    """PATCH a work item's System.Tags field with the supplied tag list."""
    _ado_request(
        "PATCH",
        organisation_url,
        pat,
        path=f"{project}/_apis/wit/workitems/{work_item_id}",
        json_body=[
            {
                "op": "add",
                "path": "/fields/System.Tags",
                "value": "; ".join(tags),
            }
        ],
        content_type="application/json-patch+json",
    )


def add_tag_to_work_item(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    work_item_id: int,
    tag: str,
) -> None:
    """Append ``tag`` to the work item's System.Tags field, preserving
    existing tags. No-op if the tag is already present.
    """
    current = _get_work_item_tags(
        organisation_url=organisation_url,
        pat=pat,
        project=project,
        work_item_id=work_item_id,
    )
    if tag in current:
        return
    _patch_work_item_tags(
        organisation_url=organisation_url,
        pat=pat,
        project=project,
        work_item_id=work_item_id,
        tags=[*current, tag],
    )


def remove_tag_from_work_item(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    work_item_id: int,
    tag: str,
) -> None:
    """Remove ``tag`` from the work item's System.Tags field, preserving
    every other tag. No-op if the tag isn't present.
    """
    current = _get_work_item_tags(
        organisation_url=organisation_url,
        pat=pat,
        project=project,
        work_item_id=work_item_id,
    )
    if tag not in current:
        return
    _patch_work_item_tags(
        organisation_url=organisation_url,
        pat=pat,
        project=project,
        work_item_id=work_item_id,
        tags=[t for t in current if t != tag],
    )
```

Two things to note:

1. The `_patch_work_item_tags` helper passes `content_type="application/json-patch+json"` — ADO requires this exact content type for JSON Patch on work items. This is a new kwarg on `_ado_request`. Update `_ado_request` to accept and forward it.

Find the existing `_ado_request` signature and add the parameter (default to `None` meaning "let requests pick"):

```python
def _ado_request(
    method: str,
    organisation_url: str,
    pat: str,
    *,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | list[Any] | None = None,
    content_type: str | None = None,
) -> requests.Response:
    ...
    headers = {"Content-Type": content_type} if content_type else {}
    response = requests.request(
        method,
        url,
        auth=("", pat),
        params=query,
        json=json_body,
        headers=headers,
        timeout=AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
    )
    ...
```

Also widen the `json_body` type annotation from `dict[str, Any] | None` to `dict[str, Any] | list[Any] | None` because JSON Patch bodies are lists.

2. The split-on-semicolon parse in `_get_work_item_tags` strips whitespace (`; ` is ADO's canonical separator).

- [ ] **Step 4: Re-export from `client/__init__.py`**

Add `add_tag_to_work_item` and `remove_tag_from_work_item` to the existing import block and `__all__`.

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
feat(integrations): add work-item tag client functions to the ADO client

ADO work items expose tags via a single System.Tags field
(semicolon-separated string), not via a dedicated API. add_tag_to_work_item
and remove_tag_from_work_item implement the GET-then-PATCH dance with
two private helpers (_get_work_item_tags, _patch_work_item_tags). Both
public functions are idempotent — they no-op when the desired terminal
state already holds.

Also generalises _ado_request to accept a content_type kwarg (ADO
requires "application/json-patch+json" for work-item PATCH bodies)
and widens json_body's typing to accept list bodies (JSON Patch).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Labels service module

**Files:**
- Create: `api/integrations/azure_devops/services/labels.py`
- Create: `api/tests/unit/integrations/azure_devops/test_labels.py`

The service exposes two public functions:

- `apply_flagsmith_label_to_resource(resource: FeatureExternalResource) -> None` — load config; if `labeling_enabled`, parse URL, call right client function.
- `remove_flagsmith_label_from_resource(*, project_id, resource_url, resource_type) -> None` — same pattern, takes fields directly because the FER row may be gone.

Both are gated by `labeling_enabled` and catch `requests.RequestException` to log + return (never raise).

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_labels.py` with:

```python
import pytest
import responses

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.labels import (
    apply_flagsmith_label_to_resource,
    remove_flagsmith_label_from_resource,
)

ORG_URL = "https://dev.azure.com/test-org"


@pytest.mark.django_db
@responses.activate
def test_apply_label__pr_resource_and_labeling_enabled__posts_label(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/labels",
        json={"id": "x", "name": "flagsmith"},
    )

    # When
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_apply_label__labeling_disabled__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — labeling_enabled defaults to False
    assert azure_devops_configuration.labeling_enabled is False

    # When
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_apply_label__no_configuration__noop(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — no configuration exists

    # When
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_apply_label__work_item_resource__patches_tags(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    import re

    match = re.search(
        r"_workitems/edit/(\d+)",
        azure_devops_work_item_resource_open.url,
    )
    assert match is not None
    work_item_id = int(match.group(1))

    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/{work_item_id}",
        json={"id": work_item_id, "fields": {}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/{work_item_id}",
        json={"id": work_item_id, "fields": {"System.Tags": "flagsmith"}},
    )

    # When
    apply_flagsmith_label_to_resource(azure_devops_work_item_resource_open)

    # Then
    assert len(responses.calls) == 2


@pytest.mark.django_db
@responses.activate
def test_apply_label__ado_500__logs_and_returns(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/1/labels",
        json={},
        status=500,
    )

    # When — must not raise
    apply_flagsmith_label_to_resource(azure_devops_pr_resource_open)

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_remove_label__pr_resource_and_labeling_enabled__deletes(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.delete(
        f"{ORG_URL}/proj/_apis/git/pullrequests/77/labels/flagsmith",
        json={},
        status=204,
    )

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_remove_label__labeling_disabled__noop(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given — labeling_enabled defaults to False

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_remove_label__no_configuration__noop(
    feature: Feature,
) -> None:
    # Given — no configuration

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/77"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
@responses.activate
def test_remove_label__work_item_resource__patches_filtered_tags(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.labeling_enabled = True
    azure_devops_configuration.save()
    responses.get(
        f"{ORG_URL}/proj/_apis/wit/workitems/200",
        json={"id": 200, "fields": {"System.Tags": "alpha; flagsmith"}},
    )
    responses.patch(
        f"{ORG_URL}/proj/_apis/wit/workitems/200",
        json={"id": 200, "fields": {"System.Tags": "alpha"}},
    )

    # When
    remove_flagsmith_label_from_resource(
        project_id=feature.project_id,
        resource_url="https://dev.azure.com/test-org/proj/_workitems/edit/200",
        resource_type="AZURE_DEVOPS_WORK_ITEM",
    )

    # Then
    assert len(responses.calls) == 2
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_labels.py -v'
```

Expected: collection error.

- [ ] **Step 3: Create the labels service**

Create `api/integrations/azure_devops/services/labels.py` with the following exact contents:

```python
import requests
import structlog

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.azure_devops.client import (
    add_tag_to_pull_request,
    add_tag_to_work_item,
    remove_tag_from_pull_request,
    remove_tag_from_work_item,
)
from integrations.azure_devops.constants import AZURE_DEVOPS_FLAGSMITH_LABEL
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.url_parsing import (
    parse_pull_request_url,
    parse_work_item_url,
)

logger = structlog.get_logger("azure_devops")


def _config_for_project(project_id: int) -> AzureDevOpsConfiguration | None:
    """Load the AzureDevOpsConfiguration with labeling_enabled set, or
    return None.
    """
    config: AzureDevOpsConfiguration | None = (
        AzureDevOpsConfiguration.objects.filter(project_id=project_id).first()
    )
    if not config or not config.labeling_enabled:
        return None
    return config


def apply_flagsmith_label_to_resource(
    resource: FeatureExternalResource,
) -> None:
    """Apply the "flagsmith" label/tag to the linked ADO resource. No-op
    if labelling is disabled or unconfigured. Never raises — failures are
    logged via ``label.apply_failed``.
    """
    config = _config_for_project(resource.feature.project_id)
    if config is None:
        return

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
        feature__id=resource.feature_id,
        resource__type=resource.type,
    )

    try:
        if resource.type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
            ref = parse_pull_request_url(resource.url)
            if ref is None:
                return
            add_tag_to_pull_request(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=ref.project,
                pull_request_id=ref.pull_request_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.applied", ado__resource__id=ref.pull_request_id)
            return

        if resource.type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
            work_ref = parse_work_item_url(resource.url)
            if work_ref is None:
                return
            add_tag_to_work_item(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=work_ref.project,
                work_item_id=work_ref.work_item_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.applied", ado__resource__id=work_ref.work_item_id)
    except requests.RequestException:
        log.exception("label.apply_failed")


def remove_flagsmith_label_from_resource(
    *,
    project_id: int,
    resource_url: str,
    resource_type: str,
) -> None:
    """Remove the "flagsmith" label/tag from the ADO resource. Takes fields
    directly because this is called from the unlink task after the FER row
    is gone. No-op if labelling is disabled or unconfigured. Never raises.
    """
    config = _config_for_project(project_id)
    if config is None:
        return

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
        resource__type=resource_type,
    )

    try:
        if resource_type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
            ref = parse_pull_request_url(resource_url)
            if ref is None:
                return
            remove_tag_from_pull_request(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=ref.project,
                pull_request_id=ref.pull_request_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.removed", ado__resource__id=ref.pull_request_id)
            return

        if resource_type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
            work_ref = parse_work_item_url(resource_url)
            if work_ref is None:
                return
            remove_tag_from_work_item(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=work_ref.project,
                work_item_id=work_ref.work_item_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.removed", ado__resource__id=work_ref.work_item_id)
    except requests.RequestException:
        log.exception("label.removal_failed")
```

- [ ] **Step 4: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_labels.py -v'
make typecheck
make lint
```

Expected: 9 passed; mypy + lint clean.

- [ ] **Step 5: Commit**

```bash
git add api/integrations/azure_devops/services/labels.py api/tests/unit/integrations/azure_devops/test_labels.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps labels service

Two public functions:
- apply_flagsmith_label_to_resource(resource) parses the URL, dispatches
  to the right client function (PR labels API or work-item Tags PATCH),
  and applies the "flagsmith" tag.
- remove_flagsmith_label_from_resource(...) takes fields directly so it
  can be called from the unlink task after the FER row is gone.

Both are gated by labeling_enabled and never raise — requests.RequestException
is caught and logged as label.apply_failed / label.removal_failed.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Task wrappers

**Files:**
- Modify: `api/integrations/azure_devops/tasks.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_tasks.py`

- [ ] **Step 1: Append the failing task tests**

Append to `api/tests/unit/integrations/azure_devops/test_tasks.py`:

```python
from integrations.azure_devops.tasks import (
    apply_azure_devops_label,
    remove_azure_devops_label,
)


@pytest.mark.django_db
def test_apply_label_task__valid_id__forwards_to_service(
    azure_devops_pr_resource_open: FeatureExternalResource,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.apply_flagsmith_label_to_resource"
    )

    # When
    apply_azure_devops_label(azure_devops_pr_resource_open.id)

    # Then
    service_mock.assert_called_once_with(azure_devops_pr_resource_open)


@pytest.mark.django_db
def test_apply_label_task__missing_resource__noop(
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.apply_flagsmith_label_to_resource"
    )

    # When
    apply_azure_devops_label(999999)

    # Then
    service_mock.assert_not_called()


@pytest.mark.django_db
def test_remove_label_task__valid_args__forwards_to_service(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    service_mock = mocker.patch(
        "integrations.azure_devops.tasks.remove_flagsmith_label_from_resource"
    )

    # When
    remove_azure_devops_label(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )

    # Then
    service_mock.assert_called_once_with(
        project_id=feature.project_id,
        resource_url=(
            "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1"
        ),
        resource_type="AZURE_DEVOPS_PULL_REQUEST",
    )
```

- [ ] **Step 2: Run to verify failure**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_tasks.py -k label -v'
```

Expected: ImportErrors.

- [ ] **Step 3: Append the task wrappers**

Append to `api/integrations/azure_devops/tasks.py`:

```python
from integrations.azure_devops.services.labels import (
    apply_flagsmith_label_to_resource,
    remove_flagsmith_label_from_resource,
)


@register_task_handler()
def apply_azure_devops_label(resource_id: int) -> None:
    """Apply the "flagsmith" label/tag to the linked ADO resource.
    Dispatched at link time. No-op if labelling is disabled.
    """
    try:
        resource = FeatureExternalResource.objects.get(id=resource_id)
    except FeatureExternalResource.DoesNotExist:
        return
    apply_flagsmith_label_to_resource(resource)


@register_task_handler()
def remove_azure_devops_label(
    *,
    project_id: int,
    resource_url: str,
    resource_type: str,
) -> None:
    """Remove the "flagsmith" label/tag from the ADO resource.
    Dispatched at unlink time. Takes fields directly because the FER row
    is gone.
    """
    remove_flagsmith_label_from_resource(
        project_id=project_id,
        resource_url=resource_url,
        resource_type=resource_type,
    )
```

The two new service imports should be added to the existing import block at the top of `tasks.py`.

- [ ] **Step 4: Run tests + mypy + lint**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_tasks.py -v'
make typecheck
make lint
```

Expected: 9 passed (6 from PR 6 + 3 new); mypy + lint clean.

- [ ] **Step 5: Commit**

```bash
git add api/integrations/azure_devops/tasks.py api/tests/unit/integrations/azure_devops/test_tasks.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps label task wrappers

Two @register_task_handler() decorated wrappers:
- apply_azure_devops_label(resource_id): loads the FER and forwards to
  apply_flagsmith_label_to_resource.
- remove_azure_devops_label(project_id, resource_url, resource_type):
  takes fields directly (FER may be gone by run time).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Full-suite verification

- [ ] **Step 1: Lint, typecheck, ADO tests, regression guard, migrations**

```bash
cd api
make lint
make typecheck
make test opts='-n0 tests/unit/integrations/azure_devops/ -v'
make test opts='tests/unit/integrations/gitlab tests/unit/integrations/github tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/features/test_migrations.py'
make django-make-migrations opts='--check --dry-run'
```

Expected: all clean; ~225 ADO tests pass (PR 6 baseline 198 + 9 PR + 6 WI + 9 labels + 3 tasks ≈ 225); regression suite passes; no migration drift.

- [ ] **Step 2: Branch state**

```bash
git status
git log --oneline feat/azure-devops-06-comments..HEAD
```

Expected: working tree clean; 4 feature commits on this branch ahead of `feat/azure-devops-06-comments`, plus the plan-doc commit at the base.

---

## Done condition

- Branch `feat/azure-devops-07-labels` carries the PR 7 plan-doc commit plus four feature commits.
- The Flagsmith → ADO labelling layer is callable but not yet invoked from anywhere (dispatcher wiring is a later PR).
- All new tests pass; mypy strict, ruff, `flagsmith-lint-tests` clean.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-06-comments`.
