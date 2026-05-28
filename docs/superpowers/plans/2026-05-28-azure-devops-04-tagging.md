# Azure DevOps Integration — PR 4: Tagging service

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Flagsmith-side tagging that reflects the state of linked Azure DevOps pull requests and work items on the feature itself: a `TagType.AZURE_DEVOPS` system-tag library, a mapper from resource metadata + state to a tag label, and a tagging service that the link / unlink / webhook flows in later PRs will call.

**Architecture:** Mirror the GitLab tagging shape closely — an enum of tag labels, lookup dicts keyed on kind / label / resource type, a Pydantic-validated metadata TypedDict, and three service entry points (`apply_initial_tag`, `clear_tag_for_resource`, `refresh_tags_for_resource`). All tagging operations are gated by `AzureDevOpsConfiguration.tagging_enabled`; with the toggle off, the service functions no-op silently. Tag labels follow GitLab's brevity convention — `PR Open / PR Merged / PR Abandoned / PR Draft / Work Item Open / Work Item Closed`, no `Azure` prefix. The `TagType.AZURE_DEVOPS` enum value (PR 1) is what scopes them.

**Tech Stack:** Python 3.12, Django 5.x, Pydantic (already used by the GitLab integration for metadata validation), pytest with `pytest-django`, mypy strict.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Flagsmith system tags", "Components → `services/tagging.py`", "Components → `mappers.py`", "Data model → AzureDevOpsResourceMetadata".

**Plan reference (parent):** `docs/superpowers/plans/2026-05-28-azure-devops-03-client.md`.

**Stack position:** PR 4 of N. Branches off `feat/azure-devops-03-client`. Branch name: `feat/azure-devops-04-tagging`.

---

## Design decision: tag labels drop the "Azure" prefix

The spec originally listed tag labels as `Azure PR Open / Azure PR Merged / ...`. PR 1's code reviewer flagged that the labels mixed conventions: short labels for GitLab (`Issue Open`, `MR Merged`, no vendor prefix), longer labels for Azure DevOps.

Decision: match the GitLab convention. Final tag labels:

- `PR Open`
- `PR Merged`
- `PR Abandoned`
- `PR Draft`
- `Work Item Open`
- `Work Item Closed`

Rationale:

- The `TagType.AZURE_DEVOPS` enum value scopes the source; the label doesn't need to repeat it.
- "PR" disambiguates from GitLab's "MR" naturally. "Work Item" disambiguates from GitLab's "Issue" naturally.
- Tag chips show the label only — brevity matters for UI.
- Renaming labels later means migrating system tags in user environments; lock this in now.

The spec gets updated in Task 6 to reflect this.

---

## Scope deliberately out of PR 4

- The dispatcher wiring that calls `apply_initial_tag` / `clear_tag_for_resource` from the `FeatureExternalResource` lifecycle — lands when the `vcs/services.py` dispatcher is extended (a later PR).
- The inbound webhook handler that calls `refresh_tags_for_resource` — lands in the webhook PR.
- ADO state-category enrichment via the REST client (calling `_apis/wit/workItems/{id}?fields=System.StateCategory`) — for v1 we map state strings directly using a small lookup table. If users report mis-categorisations on custom work-item types, we can revisit.
- Frontend rendering of the new tags — the existing tag UI handles all `TagType` values uniformly, so no FE work is required to display Azure tags.

---

## File Structure

- **Modify:** `api/integrations/azure_devops/constants.py` — append `AZURE_DEVOPS_TAG_COLOR`, `AzureDevOpsTagLabel` enum, three lookup dicts (`AZURE_DEVOPS_TAG_KIND_BY_LABEL`, `AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE`, `AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL`).
- **Create:** `api/integrations/azure_devops/types.py` — `AzureDevOpsResourceMetadata` TypedDict (client-supplied snapshot persisted as JSON on `FeatureExternalResource.metadata`).
- **Create:** `api/integrations/azure_devops/mappers.py` — `map_pr_state_to_tag_label`, `map_work_item_state_to_tag_label`, `map_resource_to_tag_label`.
- **Create:** `api/integrations/azure_devops/services/tagging.py` — `set_azure_devops_tag`, `apply_initial_tag`, `clear_tag_for_resource`, `refresh_tags_for_resource`.
- **Modify:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — update the "Flagsmith system tags" section to the new label set.
- **Create:** `api/tests/unit/integrations/azure_devops/test_mappers.py`.
- **Create:** `api/tests/unit/integrations/azure_devops/test_tagging.py`.
- **Modify:** `api/tests/unit/integrations/azure_devops/test_constants.py` — append tests for the new constants/enum.

No other files are touched.

---

## Pre-flight

- [ ] **Step 0: Confirm working branch**

```bash
cd /Users/asaphkotzin/Dev/flagsmith
git status
git log --oneline -3
```

Expected: branch `feat/azure-devops-04-tagging`, HEAD at PR 3's tip (`b24ca9caf`). Working tree clean. If the branch does not exist, create it off `feat/azure-devops-03-client`:

```bash
git checkout feat/azure-devops-03-client
git checkout -b feat/azure-devops-04-tagging
```

---

## Task 1: Constants — colour, label enum, lookup dicts

**Files:**
- Modify: `api/integrations/azure_devops/constants.py`
- Modify: `api/tests/unit/integrations/azure_devops/test_constants.py`

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_constants.py`:

```python
from features.feature_external_resources.models import ResourceType
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_TAG_COLOR,
    AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE,
    AzureDevOpsTagLabel,
)


def test_tag_color__shape__is_hex_string() -> None:
    # Given
    colour = AZURE_DEVOPS_TAG_COLOR

    # When
    is_hex = isinstance(colour, str) and colour.startswith("#") and len(colour) == 7

    # Then
    assert is_hex


def test_tag_label_enum__members__are_short_human_labels() -> None:
    # Given
    expected = {
        "PR Open",
        "PR Merged",
        "PR Abandoned",
        "PR Draft",
        "Work Item Open",
        "Work Item Closed",
    }

    # When
    actual = {member.value for member in AzureDevOpsTagLabel}

    # Then
    assert actual == expected


def test_kind_by_label__all_members__map_to_pr_or_work_item() -> None:
    # Given
    valid_kinds = {"PR", "Work Item"}

    # When
    kinds = set(AZURE_DEVOPS_TAG_KIND_BY_LABEL.values())

    # Then
    assert kinds <= valid_kinds
    assert set(AZURE_DEVOPS_TAG_KIND_BY_LABEL.keys()) == set(AzureDevOpsTagLabel)


def test_kind_by_resource_type__keys__cover_both_azure_devops_resource_types() -> None:
    # Given
    expected_keys = {
        ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        ResourceType.AZURE_DEVOPS_WORK_ITEM.value,
    }

    # When
    actual_keys = set(AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE.keys())

    # Then
    assert actual_keys == expected_keys


def test_description_by_label__keys__cover_every_member() -> None:
    # Given
    expected_keys = set(AzureDevOpsTagLabel)

    # When
    actual_keys = set(AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL.keys())

    # Then
    assert actual_keys == expected_keys
```

- [ ] **Step 2: Run the tests to verify they fail**

From `api/`:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_constants.py -v'
```

Expected: import errors at collection.

- [ ] **Step 3: Append to the constants module**

The current `api/integrations/azure_devops/constants.py` is:

```python
AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS = 10

AZURE_DEVOPS_API_VERSION = "7.1"
```

Replace with:

```python
from enum import Enum

from features.feature_external_resources.models import ResourceType

AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS = 10

AZURE_DEVOPS_API_VERSION = "7.1"

AZURE_DEVOPS_TAG_COLOR = "#0078D4"


class AzureDevOpsTagLabel(Enum):
    PR_OPEN = "PR Open"
    PR_MERGED = "PR Merged"
    PR_ABANDONED = "PR Abandoned"
    PR_DRAFT = "PR Draft"
    WORK_ITEM_OPEN = "Work Item Open"
    WORK_ITEM_CLOSED = "Work Item Closed"


AZURE_DEVOPS_TAG_KIND_BY_LABEL: dict[AzureDevOpsTagLabel, str] = {
    AzureDevOpsTagLabel.PR_OPEN: "PR",
    AzureDevOpsTagLabel.PR_MERGED: "PR",
    AzureDevOpsTagLabel.PR_ABANDONED: "PR",
    AzureDevOpsTagLabel.PR_DRAFT: "PR",
    AzureDevOpsTagLabel.WORK_ITEM_OPEN: "Work Item",
    AzureDevOpsTagLabel.WORK_ITEM_CLOSED: "Work Item",
}


AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE: dict[str, str] = {
    ResourceType.AZURE_DEVOPS_PULL_REQUEST.value: "PR",
    ResourceType.AZURE_DEVOPS_WORK_ITEM.value: "Work Item",
}


AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL: dict[AzureDevOpsTagLabel, str] = {
    AzureDevOpsTagLabel.PR_OPEN: "Has a linked Azure DevOps pull request open",
    AzureDevOpsTagLabel.PR_MERGED: "Has a linked Azure DevOps pull request merged",
    AzureDevOpsTagLabel.PR_ABANDONED: "Has a linked Azure DevOps pull request abandoned",
    AzureDevOpsTagLabel.PR_DRAFT: "Has a linked Azure DevOps pull request in draft",
    AzureDevOpsTagLabel.WORK_ITEM_OPEN: "Has a linked Azure DevOps work item open",
    AzureDevOpsTagLabel.WORK_ITEM_CLOSED: "Has a linked Azure DevOps work item closed",
}
```

The colour `#0078D4` is Microsoft's "Azure Blue" — distinct from GitLab's `#FC6D26` (orange) and GitHub's existing colour, so the chips don't visually clash.

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_constants.py -v'
```

Expected: 7 passed (2 from PR 3 + 5 new).

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/constants.py api/tests/unit/integrations/azure_devops/test_constants.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps tag-label enum and lookup dicts

Six AzureDevOpsTagLabel members covering PR + Work Item state, plus the
lookup tables the tagging service needs (kind-by-label,
kind-by-resource-type, description-by-label). Tag colour is Microsoft
"Azure Blue" (#0078D4) so the chips read distinctly from GitLab's
orange and the GitHub palette.

Tag labels deliberately omit the "Azure" prefix to match GitLab's
brevity convention — TagType.AZURE_DEVOPS scopes them at the type
layer, and "PR" / "Work Item" already disambiguate from GitLab's "MR"
/ "Issue".

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `AzureDevOpsResourceMetadata` TypedDict

**Files:**
- Create: `api/integrations/azure_devops/types.py`

This module is small enough that no behaviour tests are required; the TypedDict is consumed by tests for the mapper in Task 3. Skip a separate test file.

- [ ] **Step 1: Create the types module**

Create `api/integrations/azure_devops/types.py` with the following exact contents:

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
```

(Mirrors GitLab's `GitLabResourceMetadata` shape from `api/integrations/gitlab/types.py`.)

- [ ] **Step 2: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 3: Commit**

```bash
git add api/integrations/azure_devops/types.py
git commit -m "$(cat <<'EOF'
feat(integrations): add AzureDevOpsResourceMetadata TypedDict

Schema for the JSON metadata snapshot the frontend supplies at
resource-link time. The mapper in the next commit validates and
extracts fields from this shape. Mirrors GitLab's
GitLabResourceMetadata.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Mappers — resource metadata + state → tag label

**Files:**
- Create: `api/integrations/azure_devops/mappers.py`
- Create: `api/tests/unit/integrations/azure_devops/test_mappers.py`

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_mappers.py` with the following exact contents:

```python
import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.azure_devops.constants import AzureDevOpsTagLabel
from integrations.azure_devops.mappers import (
    map_pr_state_to_tag_label,
    map_resource_to_tag_label,
    map_work_item_state_to_tag_label,
)


@pytest.mark.parametrize(
    "state, is_draft, expected",
    [
        ("active", False, AzureDevOpsTagLabel.PR_OPEN),
        ("active", True, AzureDevOpsTagLabel.PR_DRAFT),
        ("completed", False, AzureDevOpsTagLabel.PR_MERGED),
        ("completed", True, AzureDevOpsTagLabel.PR_MERGED),
        ("abandoned", False, AzureDevOpsTagLabel.PR_ABANDONED),
        ("abandoned", True, AzureDevOpsTagLabel.PR_ABANDONED),
        # ADO sometimes capitalises; be permissive
        ("Active", False, AzureDevOpsTagLabel.PR_OPEN),
        ("Completed", False, AzureDevOpsTagLabel.PR_MERGED),
        ("ABANDONED", False, AzureDevOpsTagLabel.PR_ABANDONED),
    ],
)
def test_map_pr_state__known_state__returns_expected_label(
    state: str, is_draft: bool, expected: AzureDevOpsTagLabel
) -> None:
    # Given
    pr_state = state

    # When
    result = map_pr_state_to_tag_label(pr_state, is_draft=is_draft)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "state",
    [
        "",
        "unknown",
        "in-progress",
        "Reviewing",
    ],
)
def test_map_pr_state__unknown_state__returns_none(state: str) -> None:
    # Given
    pr_state = state

    # When
    result = map_pr_state_to_tag_label(pr_state, is_draft=False)

    # Then
    assert result is None


def test_map_pr_state__none_state__returns_none() -> None:
    # Given
    pr_state = None

    # When
    result = map_pr_state_to_tag_label(pr_state, is_draft=False)

    # Then
    assert result is None


@pytest.mark.parametrize(
    "state, expected",
    [
        # In-progress states (ADO state-category: Proposed / InProgress / Resolved)
        ("New", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Active", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("To Do", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("In Progress", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Doing", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Approved", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Committed", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Open", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Resolved", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        # Terminal states (ADO state-category: Completed / Removed)
        ("Closed", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
        ("Done", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
        ("Removed", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
        # Case-insensitive
        ("active", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("CLOSED", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
    ],
)
def test_map_work_item_state__known_state__returns_expected_label(
    state: str, expected: AzureDevOpsTagLabel
) -> None:
    # Given
    work_item_state = state

    # When
    result = map_work_item_state_to_tag_label(work_item_state)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "state",
    [
        "",
        None,
        "blocked",
        "unknown-state",
    ],
)
def test_map_work_item_state__unknown_state__returns_none(state: str | None) -> None:
    # Given
    work_item_state = state

    # When
    result = map_work_item_state_to_tag_label(work_item_state)

    # Then
    assert result is None


@pytest.mark.django_db
def test_map_resource_to_tag_label__pr_active__returns_pr_open(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_pr_resource_open

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.PR_OPEN


@pytest.mark.django_db
def test_map_resource_to_tag_label__pr_active_draft__returns_pr_draft(
    azure_devops_pr_resource_draft: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_pr_resource_draft

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.PR_DRAFT


@pytest.mark.django_db
def test_map_resource_to_tag_label__pr_completed__returns_pr_merged(
    azure_devops_pr_resource_merged: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_pr_resource_merged

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.PR_MERGED


@pytest.mark.django_db
def test_map_resource_to_tag_label__work_item_active__returns_work_item_open(
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_work_item_resource_open

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.WORK_ITEM_OPEN


@pytest.mark.django_db
def test_map_resource_to_tag_label__work_item_closed__returns_work_item_closed(
    azure_devops_work_item_resource_closed: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_work_item_resource_closed

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.WORK_ITEM_CLOSED


@pytest.mark.django_db
def test_map_resource_to_tag_label__invalid_json_metadata__returns_none(
    azure_devops_configuration: object,
    feature: object,
) -> None:
    # Given
    from features.feature_external_resources.models import (
        FeatureExternalResource,
        ResourceType,
    )

    resource = FeatureExternalResource.objects.create(
        feature=feature,  # type: ignore[arg-type]
        url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata="not-valid-json",
    )

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label is None


@pytest.mark.django_db
def test_map_resource_to_tag_label__non_ado_resource_type__returns_none(
    feature: object,
) -> None:
    # Given
    from features.feature_external_resources.models import (
        FeatureExternalResource,
        ResourceType,
    )

    resource = FeatureExternalResource.objects.create(
        feature=feature,  # type: ignore[arg-type]
        url="https://gitlab.com/foo/bar/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label is None
```

The fixtures `azure_devops_pr_resource_open`, `azure_devops_pr_resource_draft`, `azure_devops_pr_resource_merged`, `azure_devops_work_item_resource_open`, `azure_devops_work_item_resource_closed` will live in the `conftest.py` for this test directory (Step 1.5 below).

- [ ] **Step 1.5: Extend the conftest with resource fixtures**

In `api/tests/unit/integrations/azure_devops/conftest.py`, the current contents are:

```python
import pytest

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@pytest.fixture()
def azure_devops_configuration(project: Project) -> AzureDevOpsConfiguration:
    return AzureDevOpsConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        organisation_url="https://dev.azure.com/test-org",
        personal_access_token="ado-test-token",
    )
```

Extend the file with two new imports (merge them into the existing import block at the top; ruff will sort them if you append them) and the helpers + fixtures below it. The full intended contents of `conftest.py` after this step:

```python
import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@pytest.fixture()
def azure_devops_configuration(project: Project) -> AzureDevOpsConfiguration:
    return AzureDevOpsConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        organisation_url="https://dev.azure.com/test-org",
        personal_access_token="ado-test-token",
    )


def _make_pr_resource(
    feature: Feature, *, state: str, is_draft: bool = False
) -> FeatureExternalResource:
    metadata = '{"state": "' + state + '", "is_draft": ' + (
        "true" if is_draft else "false"
    ) + "}"
    return FeatureExternalResource.objects.create(
        feature=feature,
        url=f"https://dev.azure.com/test-org/proj/_git/repo/pullrequest/{state}",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata=metadata,
    )


def _make_work_item_resource(
    feature: Feature, *, state: str
) -> FeatureExternalResource:
    return FeatureExternalResource.objects.create(
        feature=feature,
        url=f"https://dev.azure.com/test-org/proj/_workitems/edit/{abs(hash(state)) % 10000}",
        type=ResourceType.AZURE_DEVOPS_WORK_ITEM.value,
        metadata='{"state": "' + state + '"}',
    )


@pytest.fixture()
def azure_devops_pr_resource_open(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, state="active", is_draft=False)


@pytest.fixture()
def azure_devops_pr_resource_draft(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, state="active", is_draft=True)


@pytest.fixture()
def azure_devops_pr_resource_merged(feature: Feature) -> FeatureExternalResource:
    return _make_pr_resource(feature, state="completed")


@pytest.fixture()
def azure_devops_work_item_resource_open(feature: Feature) -> FeatureExternalResource:
    return _make_work_item_resource(feature, state="Active")


@pytest.fixture()
def azure_devops_work_item_resource_closed(
    feature: Feature,
) -> FeatureExternalResource:
    return _make_work_item_resource(feature, state="Closed")
```

The `feature` fixture is already provided by the repo's root `conftest.py`. The `_make_*` helpers are module-local (not pytest fixtures) — they encapsulate the JSON-metadata construction so each fixture is one-line.

- [ ] **Step 2: Run the tests to verify they fail**

From `api/`:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_mappers.py -v'
```

Expected: collection error — `integrations.azure_devops.mappers` does not exist yet.

- [ ] **Step 3: Create the mappers module**

Create `api/integrations/azure_devops/mappers.py` with the following exact contents:

```python
from pydantic import TypeAdapter, ValidationError

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.azure_devops.constants import AzureDevOpsTagLabel
from integrations.azure_devops.types import AzureDevOpsResourceMetadata

_resource_metadata_adapter: TypeAdapter[AzureDevOpsResourceMetadata] = TypeAdapter(
    AzureDevOpsResourceMetadata,
)


# ADO state strings are case-insensitive in practice; lowercase the lookup keys
# and lowercase the incoming string before checking.
_PR_OPEN_STATES = {"active"}
_PR_MERGED_STATES = {"completed"}
_PR_ABANDONED_STATES = {"abandoned"}


_WORK_ITEM_OPEN_STATES = {
    "new",
    "active",
    "to do",
    "in progress",
    "doing",
    "approved",
    "committed",
    "open",
    "resolved",
}
_WORK_ITEM_CLOSED_STATES = {"closed", "done", "removed"}


def map_pr_state_to_tag_label(
    state: str | None,
    *,
    is_draft: bool,
) -> AzureDevOpsTagLabel | None:
    """Map an Azure DevOps pull-request state (+ draft flag) to a Flagsmith
    tag label, or ``None`` if the state is unknown.
    """
    if not state:
        return None
    normalised = state.lower()
    if normalised in _PR_ABANDONED_STATES:
        return AzureDevOpsTagLabel.PR_ABANDONED
    if normalised in _PR_MERGED_STATES:
        return AzureDevOpsTagLabel.PR_MERGED
    if normalised in _PR_OPEN_STATES:
        return AzureDevOpsTagLabel.PR_DRAFT if is_draft else AzureDevOpsTagLabel.PR_OPEN
    return None


def map_work_item_state_to_tag_label(
    state: str | None,
) -> AzureDevOpsTagLabel | None:
    """Map an Azure DevOps work-item state to a Flagsmith tag label, or
    ``None`` if the state is unknown. Covers the common states across
    Agile, Scrum, and Basic process templates.
    """
    if not state:
        return None
    normalised = state.lower()
    if normalised in _WORK_ITEM_CLOSED_STATES:
        return AzureDevOpsTagLabel.WORK_ITEM_CLOSED
    if normalised in _WORK_ITEM_OPEN_STATES:
        return AzureDevOpsTagLabel.WORK_ITEM_OPEN
    return None


def map_resource_to_tag_label(
    resource: FeatureExternalResource,
) -> AzureDevOpsTagLabel | None:
    """Derive the Azure DevOps tag label for ``resource.feature`` from the
    JSON metadata snapshot the client supplied at link time. Returns
    ``None`` if the metadata is missing, malformed, or the state isn't
    recognised.
    """
    try:
        metadata = _resource_metadata_adapter.validate_json(resource.metadata or "")
    except ValidationError:
        return None
    state = metadata.get("state")
    if resource.type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
        return map_pr_state_to_tag_label(
            state,
            is_draft=bool(metadata.get("is_draft")),
        )
    if resource.type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
        return map_work_item_state_to_tag_label(state)
    return None
```

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_mappers.py -v'
```

Expected: all parametrised cases pass — around 30 (9 PR known + 4 PR unknown + 1 PR none + 13 work-item known + 4 work-item unknown + 5 resource happy-paths + 2 resource edge-cases).

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Run lint**

```bash
make lint
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/mappers.py api/tests/unit/integrations/azure_devops/test_mappers.py api/tests/unit/integrations/azure_devops/conftest.py
git commit -m "$(cat <<'EOF'
feat(integrations): map Azure DevOps state to tag labels

Three mappers:

- map_pr_state_to_tag_label(state, *, is_draft) covers active /
  completed / abandoned states, with is_draft overriding "active" to
  PR_DRAFT.
- map_work_item_state_to_tag_label(state) covers the common states
  across ADO's Agile / Scrum / Basic process templates. Unknown states
  return None (fail-closed — the tagging service treats None as "no
  tag change").
- map_resource_to_tag_label(resource) is the high-level entry point
  that pydantic-validates the metadata snapshot stored on the
  FeatureExternalResource and dispatches to the right state mapper.

State lookups are case-insensitive. Mirrors the GitLab mapper shape.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Tagging service

**Files:**
- Create: `api/integrations/azure_devops/services/tagging.py`
- Create: `api/tests/unit/integrations/azure_devops/test_tagging.py`

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/test_tagging.py` with the following exact contents:

```python
import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.tagging import (
    apply_initial_tag,
    clear_tag_for_resource,
    refresh_tags_for_resource,
)
from projects.tags.models import Tag, TagType


def _ado_labels_on(feature: Feature) -> list[str]:
    return sorted(
        feature.tags.filter(type=TagType.AZURE_DEVOPS.value).values_list(
            "label", flat=True
        )
    )


@pytest.mark.django_db
def test_apply_initial_tag__pr_open__adds_pr_open_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]


@pytest.mark.django_db
def test_apply_initial_tag__work_item_open__adds_work_item_open_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_work_item_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_work_item_resource_open.feature) == [
        "Work Item Open"
    ]


@pytest.mark.django_db
def test_apply_initial_tag__tagging_disabled__no_op(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — tagging_enabled defaults to False
    assert azure_devops_configuration.tagging_enabled is False

    # When
    apply_initial_tag(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == []


@pytest.mark.django_db
def test_apply_initial_tag__no_configuration__no_op(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — no AzureDevOpsConfiguration exists for this project

    # When
    apply_initial_tag(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == []


@pytest.mark.django_db
def test_apply_initial_tag__pr_then_work_item__both_tags_coexist(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_pr_resource_open)
    apply_initial_tag(azure_devops_work_item_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == [
        "PR Open",
        "Work Item Open",
    ]


@pytest.mark.django_db
def test_apply_initial_tag__pr_open_then_pr_merged__same_kind_is_replaced(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_pr_resource_merged: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_pr_resource_open)
    apply_initial_tag(azure_devops_pr_resource_merged)

    # Then — the PR_OPEN tag was replaced by PR_MERGED
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Merged"]


@pytest.mark.django_db
def test_clear_tag_for_resource__only_resource_of_kind__removes_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]

    # When
    clear_tag_for_resource(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == []


@pytest.mark.django_db
def test_clear_tag_for_resource__other_resource_of_same_kind__keeps_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    first = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata='{"state": "active", "is_draft": false}',
    )
    second = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/2",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata='{"state": "active", "is_draft": false}',
    )
    apply_initial_tag(first)

    # When
    clear_tag_for_resource(first)

    # Then — the PR Open tag persists because `second` is still linked
    assert second.pk != first.pk
    assert _ado_labels_on(feature) == ["PR Open"]


@pytest.mark.django_db
def test_clear_tag_for_resource__different_kind__keeps_other_kinds_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    apply_initial_tag(azure_devops_work_item_resource_open)

    # When — clear only the PR resource
    clear_tag_for_resource(azure_devops_pr_resource_open)

    # Then — Work Item tag persists
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["Work Item Open"]


@pytest.mark.django_db
def test_clear_tag_for_resource__non_ado_resource__no_op(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    gitlab_resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.com/foo/bar/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    clear_tag_for_resource(gitlab_resource)

    # Then — no exception, no ADO tags created or removed
    assert _ado_labels_on(feature) == []


@pytest.mark.django_db
def test_refresh_tags_for_resource__state_change__rotates_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]
    # Caller (the webhook handler in a later PR) updates metadata before
    # calling refresh:
    azure_devops_pr_resource_open.metadata = (
        '{"state": "completed", "is_draft": false}'
    )
    azure_devops_pr_resource_open.save()

    # When
    refresh_tags_for_resource(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Merged"]


@pytest.mark.django_db
def test_refresh_tags_for_resource__unknown_state__no_op(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    azure_devops_pr_resource_open.metadata = '{"state": "weird", "is_draft": false}'
    azure_devops_pr_resource_open.save()

    # When
    refresh_tags_for_resource(azure_devops_pr_resource_open)

    # Then — unknown state leaves the existing tag intact rather than
    # blindly clearing it.
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]
```

The fixtures `azure_devops_pr_resource_open` etc. come from `conftest.py` (added in Task 3 Step 1.5).

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_tagging.py -v'
```

Expected: collection error — module not found.

- [ ] **Step 3: Create the tagging service**

Create `api/integrations/azure_devops/services/tagging.py` with the following exact contents:

```python
from features.feature_external_resources.models import (
    FeatureExternalResource,
)
from features.models import Feature
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_TAG_COLOR,
    AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE,
    AzureDevOpsTagLabel,
)
from integrations.azure_devops.mappers import map_resource_to_tag_label
from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.tags.models import Tag, TagType


def _tagging_enabled_for_resource(resource: FeatureExternalResource) -> bool:
    """True if the resource's project has an AzureDevOpsConfiguration with
    tagging_enabled set. False if there's no configuration or the toggle
    is off.
    """
    config = AzureDevOpsConfiguration.objects.filter(
        project=resource.feature.project,
    ).first()
    return bool(config and config.tagging_enabled)


def set_azure_devops_tag(feature: Feature, new_label: AzureDevOpsTagLabel) -> None:
    """Apply an Azure DevOps system tag to ``feature``, replacing any
    existing Azure DevOps tag of the same kind (PR / Work Item) first.
    """
    kind = AZURE_DEVOPS_TAG_KIND_BY_LABEL[new_label]
    feature.tags.remove(
        *feature.tags.filter(
            type=TagType.AZURE_DEVOPS.value,
            label__startswith=kind,
        )
    )
    tag, _ = Tag.objects.get_or_create(
        label=new_label.value,
        project=feature.project,
        is_system_tag=True,
        type=TagType.AZURE_DEVOPS.value,
        defaults={
            "color": AZURE_DEVOPS_TAG_COLOR,
            "description": AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL[new_label],
        },
    )
    feature.tags.add(tag)


def apply_initial_tag(resource: FeatureExternalResource) -> None:
    """Tag ``resource.feature`` based on the linked ADO resource's state
    at link time. No-op when the project has no AzureDevOpsConfiguration,
    when tagging_enabled is False, or when the metadata can't be mapped
    to a known label.
    """
    if not _tagging_enabled_for_resource(resource):
        return
    label = map_resource_to_tag_label(resource)
    if label is None:
        return
    set_azure_devops_tag(resource.feature, label)


def clear_tag_for_resource(resource: FeatureExternalResource) -> None:
    """Remove the Azure DevOps tag for ``resource``'s kind (PR / Work Item)
    from its feature when no other linked FeatureExternalResource of the
    same kind remains. Safe to call whether ``resource`` is still in the
    DB or has already been deleted.
    """
    kind = AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE.get(resource.type)
    if kind is None:
        return
    if (
        FeatureExternalResource.objects.filter(
            feature=resource.feature,
            type=resource.type,
        )
        .exclude(pk=resource.pk)
        .exists()
    ):
        return
    resource.feature.tags.remove(
        *resource.feature.tags.filter(
            type=TagType.AZURE_DEVOPS.value,
            label__startswith=kind,
        )
    )


def refresh_tags_for_resource(resource: FeatureExternalResource) -> None:
    """Re-apply the right tag for ``resource``'s current metadata. Called
    by the inbound-webhook handler (PR 10) after it updates the metadata
    in place. No-op when tagging is disabled or when the state can't be
    mapped to a known label.
    """
    if not _tagging_enabled_for_resource(resource):
        return
    label = map_resource_to_tag_label(resource)
    if label is None:
        return
    set_azure_devops_tag(resource.feature, label)
```

- [ ] **Step 4: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_tagging.py -v'
```

Expected: 12 passed.

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Run lint**

```bash
make lint
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/services/tagging.py api/tests/unit/integrations/azure_devops/test_tagging.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps tagging service

Four entry points:

- set_azure_devops_tag(feature, label) replaces any existing
  same-kind tag and applies the new one.
- apply_initial_tag(resource) tags the feature based on the
  metadata snapshot at link time. No-op when the project has no
  AzureDevOpsConfiguration or tagging_enabled is False.
- clear_tag_for_resource(resource) removes the kind-scoped tag when
  the unlinked resource was the last of its kind on the feature.
- refresh_tags_for_resource(resource) re-applies the right tag from
  current metadata. Called by the future inbound-webhook handler.

PR and Work Item tags coexist independently — clearing a PR resource
leaves Work Item tags intact and vice versa. Mirrors GitLab's
tagging.set_gitlab_tag / apply_initial_tag / clear_tag_for_resource.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Update the spec to reflect the new tag-label naming

**Files:**
- Modify: `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md`

- [ ] **Step 1: Locate the affected section**

The spec's "Flagsmith system tags" subsection (under "Data model") currently lists:

```
- `Azure PR Open`
- `Azure PR Merged`
- `Azure PR Abandoned`
- `Azure PR Draft`
- `Azure Work Item Open`
- `Azure Work Item Closed`
```

- [ ] **Step 2: Apply the rename**

Replace each `Azure ` prefix in the labels above so the list reads:

```
- `PR Open`
- `PR Merged`
- `PR Abandoned`
- `PR Draft`
- `Work Item Open`
- `Work Item Closed`
```

Also add a short paragraph immediately after the list explaining the rationale (mirroring the GitLab convention, brevity for tag chips, `TagType.AZURE_DEVOPS` provides source disambiguation). Something like:

> Labels deliberately omit the "Azure DevOps" prefix to match the brevity convention the GitLab tags follow (`Issue Open`, `MR Merged`). The `TagType.AZURE_DEVOPS` enum value scopes them at the type layer, and "PR" / "Work Item" already disambiguate from GitLab's "MR" / "Issue".

Do not touch any other section of the spec.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md
git commit -m "$(cat <<'EOF'
docs(superpowers): drop "Azure" prefix from system-tag labels in spec

The original spec listed labels as "Azure PR Open" etc. Implementation
matches GitLab's brevity convention (just "PR Open", "Work Item Open",
etc.) — the TagType.AZURE_DEVOPS enum value disambiguates the source
at the type layer. Update the spec so it tracks the code.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Full-suite verification

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

Expected: all tests pass. Count ~100+ (PR 3 left it at 71; this PR adds the constants enum tests + ~30 mapper tests + ~12 tagging tests).

- [ ] **Step 4: Regression guard**

```bash
make test opts='tests/unit/integrations/gitlab tests/unit/integrations/github tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/features/test_migrations.py'
```

Expected: all pass.

- [ ] **Step 5: Migration consistency**

```bash
make django-make-migrations opts='--check --dry-run'
```

Expected: `No changes detected`.

- [ ] **Step 6: Branch state**

```bash
git status
git log --oneline feat/azure-devops-03-client..HEAD
```

Expected: working tree clean; 5 feature commits + 1 spec-update commit on this branch ahead of `feat/azure-devops-03-client`.

---

## Done condition

- Branch `feat/azure-devops-04-tagging` carries the PR 4 plan-doc commit plus five feature commits (constants, types, mappers, tagging service, spec rename).
- The Azure DevOps tag-label library is live; the tagging service is callable but has no callers yet (those land when the dispatcher is extended in a later PR).
- The spec and code agree on the brief, GitLab-aligned label naming.
- All new tests pass; mypy strict, ruff, and `flagsmith-lint-tests` clean. No schema drift.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-03-client`. The next plan in the stack will be written after this PR lands — likely covering the browse endpoints (PR 5) which extend the REST client with `list_repositories`, `list_pull_requests`, `list_work_items` plus the typeahead views the frontend will call.
