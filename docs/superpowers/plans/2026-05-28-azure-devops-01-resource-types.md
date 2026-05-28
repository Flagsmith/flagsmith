# Azure DevOps Integration — PR 1: Resource types & TagType

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add foundational enum values (`AZURE_DEVOPS_PULL_REQUEST`, `AZURE_DEVOPS_WORK_ITEM`) and `TagType.AZURE_DEVOPS` so subsequent PRs in the stack can reference them. No behavioural change — pure enum extensions plus the two migrations they require.

**Architecture:** Mirror the GitLab additions exactly. Two `TextChoices` values added to `ResourceType` in `api/features/feature_external_resources/models.py`, an `AZURE_DEVOPS_RESOURCE_TYPES` tuple alongside the existing `GITLAB_RESOURCE_TYPES`, a `AZURE_DEVOPS` value added to `TagType` in `api/projects/tags/models.py`, and one hand-written migration per app to apply the new choices on the database column.

**Tech Stack:** Django 4.x, `django.db.models.TextChoices` / `Choices`, Pytest with `pytest-django`, mypy strict mode.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Data model" and "Migrations".

**Stack position:** First PR. Branches off `feat/azure-devops-spec` (which is itself off `main`). Branch name: `feat/azure-devops-01-resource-types`.

---

## File Structure

- **Modify:** `api/features/feature_external_resources/models.py` — add two `ResourceType` values and the `AZURE_DEVOPS_RESOURCE_TYPES` tuple.
- **Modify:** `api/projects/tags/models.py` — add `AZURE_DEVOPS` to `TagType`.
- **Create:** `api/features/feature_external_resources/migrations/0004_add_azure_resource_types.py` — `AlterField` for the `type` column with the expanded choice list.
- **Create:** `api/projects/tags/migrations/0010_add_azure_devops_tag_type.py` — `AlterField` for the tag `type` column with the expanded choice list.
- **Create:** `api/tests/unit/features/test_unit_feature_external_resources_models.py` — micro-tests asserting the new enum values and tuple exist (the file does not exist yet; the existing `test_unit_feature_external_resources_views.py` covers views only).
- **Create:** `api/tests/unit/projects/tags/test_unit_projects_tags_models.py` — micro-test for the new `TagType` value (the existing tag tests cover permissions and views, not the enum).

No other files are touched in this PR.

---

## Pre-flight

- [ ] **Step 0: Create the working branch**

Run from the repo root:

```bash
git checkout feat/azure-devops-spec
git checkout -b feat/azure-devops-01-resource-types
```

Expected: `Switched to a new branch 'feat/azure-devops-01-resource-types'`.

---

## Task 1: Add `AZURE_DEVOPS_PULL_REQUEST` and `AZURE_DEVOPS_WORK_ITEM` to `ResourceType`

**Files:**
- Modify: `api/features/feature_external_resources/models.py:25-38`
- Test: `api/tests/unit/features/test_unit_feature_external_resources_models.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/features/test_unit_feature_external_resources_models.py` with the following exact contents:

```python
from features.feature_external_resources.models import (
    AZURE_DEVOPS_RESOURCE_TYPES,
    GITLAB_RESOURCE_TYPES,
    ResourceType,
)


def test_resource_type__azure_devops_pull_request__has_value_and_label() -> None:
    # Given / When / Then
    assert ResourceType.AZURE_DEVOPS_PULL_REQUEST.value == "AZURE_DEVOPS_PULL_REQUEST"
    assert ResourceType.AZURE_DEVOPS_PULL_REQUEST.label == "Azure DevOps Pull Request"


def test_resource_type__azure_devops_work_item__has_value_and_label() -> None:
    # Given / When / Then
    assert ResourceType.AZURE_DEVOPS_WORK_ITEM.value == "AZURE_DEVOPS_WORK_ITEM"
    assert ResourceType.AZURE_DEVOPS_WORK_ITEM.label == "Azure DevOps Work Item"


def test_azure_devops_resource_types__contains_pull_request_and_work_item__matches_expected_set() -> None:
    # Given / When
    members = set(AZURE_DEVOPS_RESOURCE_TYPES)

    # Then
    assert members == {
        ResourceType.AZURE_DEVOPS_PULL_REQUEST,
        ResourceType.AZURE_DEVOPS_WORK_ITEM,
    }


def test_resource_type_groupings__azure_devops_and_gitlab__are_disjoint() -> None:
    # Given / When / Then
    assert set(AZURE_DEVOPS_RESOURCE_TYPES).isdisjoint(set(GITLAB_RESOURCE_TYPES))
```

- [ ] **Step 2: Run test to verify it fails**

From the `api/` directory:

```bash
make test opts='-n0 tests/unit/features/test_unit_feature_external_resources_models.py -v'
```

Expected: All four tests fail with `ImportError` / `AttributeError` on the missing `AZURE_DEVOPS_RESOURCE_TYPES` and `ResourceType.AZURE_DEVOPS_PULL_REQUEST` / `AZURE_DEVOPS_WORK_ITEM` symbols.

- [ ] **Step 3: Add the enum members and the tuple**

In `api/features/feature_external_resources/models.py`, modify the `ResourceType` class (currently at line 25) and add the tuple alongside the existing `GITLAB_RESOURCE_TYPES`. Replace the existing block:

```python
class ResourceType(models.TextChoices):
    # GitHub external resource types
    GITHUB_ISSUE = "GITHUB_ISSUE", "GitHub Issue"
    GITHUB_PR = "GITHUB_PR", "GitHub PR"

    # GitLab external resource types
    GITLAB_ISSUE = "GITLAB_ISSUE", "GitLab Issue"
    GITLAB_MR = "GITLAB_MR", "GitLab MR"


GITLAB_RESOURCE_TYPES: tuple[ResourceType, ...] = (
    ResourceType.GITLAB_ISSUE,
    ResourceType.GITLAB_MR,
)
```

with:

```python
class ResourceType(models.TextChoices):
    # GitHub external resource types
    GITHUB_ISSUE = "GITHUB_ISSUE", "GitHub Issue"
    GITHUB_PR = "GITHUB_PR", "GitHub PR"

    # GitLab external resource types
    GITLAB_ISSUE = "GITLAB_ISSUE", "GitLab Issue"
    GITLAB_MR = "GITLAB_MR", "GitLab MR"

    # Azure DevOps external resource types
    AZURE_DEVOPS_PULL_REQUEST = "AZURE_DEVOPS_PULL_REQUEST", "Azure DevOps Pull Request"
    AZURE_DEVOPS_WORK_ITEM = "AZURE_DEVOPS_WORK_ITEM", "Azure DevOps Work Item"


GITLAB_RESOURCE_TYPES: tuple[ResourceType, ...] = (
    ResourceType.GITLAB_ISSUE,
    ResourceType.GITLAB_MR,
)


AZURE_DEVOPS_RESOURCE_TYPES: tuple[ResourceType, ...] = (
    ResourceType.AZURE_DEVOPS_PULL_REQUEST,
    ResourceType.AZURE_DEVOPS_WORK_ITEM,
)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
make test opts='-n0 tests/unit/features/test_unit_feature_external_resources_models.py -v'
```

Expected: All four tests pass.

- [ ] **Step 5: Run mypy on the modified file**

```bash
make typecheck
```

Expected: clean exit code, no new errors. `AZURE_DEVOPS_RESOURCE_TYPES` is typed identically to `GITLAB_RESOURCE_TYPES`, so mypy strict will accept it.

- [ ] **Step 6: Commit**

```bash
git add api/features/feature_external_resources/models.py api/tests/unit/features/test_unit_feature_external_resources_models.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps resource type enums

Add AZURE_DEVOPS_PULL_REQUEST and AZURE_DEVOPS_WORK_ITEM to ResourceType plus an
AZURE_DEVOPS_RESOURCE_TYPES tuple for downstream use, mirroring the existing
GitLab pattern. No behavioural change in this PR.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit created on `feat/azure-devops-01-resource-types`.

---

## Task 2: Add the migration that records the new `ResourceType` choices

**Files:**
- Create: `api/features/feature_external_resources/migrations/0004_add_azure_resource_types.py`

This migration updates the choice list stored in Django's migration history and widens `max_length` from 20 to 30 to accommodate the longest new value (`AZURE_DEVOPS_PULL_REQUEST`, 25 chars). No data migration required. Verification is via Django's `makemigrations --check` rather than a pytest assertion: after Task 1, the model and the migration history are out of sync, and Django will complain that there is an unrecorded change to `FeatureExternalResource.type`.

- [ ] **Step 1: Verify the migration name is not taken**

```bash
ls api/features/feature_external_resources/migrations/
```

Expected: the directory contains `0001_initial.py`, `0002_featureexternalresource_feature_ext_type_2b2068_idx.py`, `0003_add_gitlab_resource_types.py`, and no file with the `0004_` prefix. If a `0004_` prefix already exists, stop and ask the user — the stack base may have changed.

- [ ] **Step 2: Confirm Django sees the model/migration drift**

```bash
make docker-up
docker compose -f docker-compose.yml run --rm api python manage.py makemigrations --check --dry-run feature_external_resources
```

If your repo uses a different command shape for one-off Django management commands, prefer that. The `make docker-up django-make-migrations` target is the supported path — running it in `--check` mode is the goal here.

Expected: exit code 1 with a message like `Migrations for 'feature_external_resources': Alterations to the type field will not be recorded`. The presence of the drift confirms Task 1's enum extension is unmigrated.

- [ ] **Step 3: Create the migration**

Create `api/features/feature_external_resources/migrations/0004_add_azure_resource_types.py` with the following exact contents:

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feature_external_resources", "0003_add_gitlab_resource_types"),
    ]

    operations = [
        migrations.AlterField(
            model_name="featureexternalresource",
            name="type",
            field=models.CharField(
                choices=[
                    ("GITHUB_ISSUE", "GitHub Issue"),
                    ("GITHUB_PR", "GitHub PR"),
                    ("GITLAB_ISSUE", "GitLab Issue"),
                    ("GITLAB_MR", "GitLab MR"),
                    ("AZURE_DEVOPS_PULL_REQUEST", "Azure DevOps Pull Request"),
                    ("AZURE_DEVOPS_WORK_ITEM", "Azure DevOps Work Item"),
                ],
                max_length=30,
            ),
        ),
    ]
```

- [ ] **Step 4: Verify Django no longer sees drift**

```bash
docker compose -f docker-compose.yml run --rm api python manage.py makemigrations --check --dry-run feature_external_resources
```

Expected: exit code 0 and `No changes detected in app 'feature_external_resources'`. If Django still reports a diff, the hand-written migration differs from what Django expects — reconcile by editing the migration to match Django's expectation (keeping the chosen file name).

- [ ] **Step 5: Add a regression-guard test for the migrated choices**

Append to `api/tests/unit/features/test_unit_feature_external_resources_models.py`:

```python
def test_resource_type_field__choices__include_azure_values() -> None:
    # Given
    from features.feature_external_resources.models import FeatureExternalResource

    # When
    field = FeatureExternalResource._meta.get_field("type")
    choice_values = {value for value, _label in field.choices}

    # Then
    assert "AZURE_DEVOPS_PULL_REQUEST" in choice_values
    assert "AZURE_DEVOPS_WORK_ITEM" in choice_values
```

- [ ] **Step 6: Run the full new test file**

```bash
make test opts='-n0 tests/unit/features/test_unit_feature_external_resources_models.py -v'
```

Expected: all five tests pass.

- [ ] **Step 7: Commit**

```bash
git add api/features/feature_external_resources/migrations/0004_add_azure_resource_types.py api/tests/unit/features/test_unit_feature_external_resources_models.py
git commit -m "$(cat <<'EOF'
feat(integrations): migrate FeatureExternalResource.type for Azure choices

Add migration recording AZURE_DEVOPS_PULL_REQUEST and AZURE_DEVOPS_WORK_ITEM in the
choices list for the type column. No column shape change.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit created.

---

## Task 3: Add `AZURE_DEVOPS` to `TagType`

**Files:**
- Modify: `api/projects/tags/models.py:7-12`
- Test: `api/tests/unit/projects/tags/test_unit_projects_tags_models.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/projects/tags/test_unit_projects_tags_models.py` with the following exact contents:

```python
from projects.tags.models import TagType


def test_tag_type__azure_devops__has_value() -> None:
    # Given / When / Then
    assert TagType.AZURE_DEVOPS.value == "AZURE_DEVOPS"


def test_tag_type__members__include_existing_and_azure() -> None:
    # Given
    values = {member.value for member in TagType}

    # Then
    assert values == {"NONE", "STALE", "GITHUB", "UNHEALTHY", "GITLAB", "AZURE_DEVOPS"}
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
make test opts='-n0 tests/unit/projects/tags/test_unit_projects_tags_models.py -v'
```

Expected: both tests fail with `AttributeError: AZURE_DEVOPS` / membership mismatch.

- [ ] **Step 3: Add the enum value**

In `api/projects/tags/models.py`, modify lines 7-12. Replace:

```python
class TagType(models.Choices):
    NONE = "NONE"
    STALE = "STALE"
    GITHUB = "GITHUB"
    UNHEALTHY = "UNHEALTHY"
    GITLAB = "GITLAB"
```

with:

```python
class TagType(models.Choices):
    NONE = "NONE"
    STALE = "STALE"
    GITHUB = "GITHUB"
    UNHEALTHY = "UNHEALTHY"
    GITLAB = "GITLAB"
    AZURE_DEVOPS = "AZURE_DEVOPS"
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
make test opts='-n0 tests/unit/projects/tags/test_unit_projects_tags_models.py -v'
```

Expected: both tests pass.

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/projects/tags/models.py api/tests/unit/projects/tags/test_unit_projects_tags_models.py
git commit -m "$(cat <<'EOF'
feat(tags): add AZURE_DEVOPS TagType

Add the AZURE_DEVOPS TagType so the Azure DevOps integration can tag
features with system tags reflecting upstream PR / work-item state in
later PRs.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit created.

---

## Task 4: Add the migration that records the new `TagType` choices

**Files:**
- Create: `api/projects/tags/migrations/0010_add_azure_devops_tag_type.py`

Same pattern as Task 2: verification is via `makemigrations --check`, not via pytest. A regression-guard test on `Tag._meta.get_field("type").choices` is added after the migration is in place.

- [ ] **Step 1: Verify the migration name is not taken**

```bash
ls api/projects/tags/migrations/
```

Expected: the directory contains files numbered up to `0009_add_gitlab_tag_type.py` and no file with the `0010_` prefix. If a `0010_` prefix already exists, stop and ask the user.

- [ ] **Step 2: Confirm Django sees the model/migration drift**

```bash
docker compose -f docker-compose.yml run --rm api python manage.py makemigrations --check --dry-run tags
```

Expected: exit code 1. Django reports an unrecorded change on `Tag.type`'s choice list.

- [ ] **Step 3: Create the migration**

Create `api/projects/tags/migrations/0010_add_azure_devops_tag_type.py` with the following exact contents:

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tags", "0009_add_gitlab_tag_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="type",
            field=models.CharField(
                choices=[
                    ("NONE", "None"),
                    ("STALE", "Stale"),
                    ("GITHUB", "Github"),
                    ("UNHEALTHY", "Unhealthy"),
                    ("GITLAB", "Gitlab"),
                    ("AZURE_DEVOPS", "Azure Devops"),
                ],
                default="NONE",
                help_text="Field used to provide a consistent identifier for the FE and API to use for business logic.",
                max_length=100,
            ),
        ),
    ]
```

The label `"Azure Devops"` matches Django's default human-readable rendering of `AZURE_DEVOPS` and matches the casing pattern of the existing `"Github"`, `"Gitlab"`, `"None"`, `"Stale"`, `"Unhealthy"` entries in `0009_add_gitlab_tag_type.py`.

- [ ] **Step 4: Verify Django no longer sees drift**

```bash
docker compose -f docker-compose.yml run --rm api python manage.py makemigrations --check --dry-run tags
```

Expected: exit code 0 and `No changes detected in app 'tags'`. If Django reports a diff, reconcile by editing the migration to match.

- [ ] **Step 5: Add a regression-guard test for the migrated choices**

Append to `api/tests/unit/projects/tags/test_unit_projects_tags_models.py`:

```python
def test_tag_type_field__choices__include_azure_devops() -> None:
    # Given
    from projects.tags.models import Tag

    # When
    field = Tag._meta.get_field("type")
    choice_values = {value for value, _label in field.choices}

    # Then
    assert "AZURE_DEVOPS" in choice_values
```

- [ ] **Step 6: Run the full test file**

```bash
make test opts='-n0 tests/unit/projects/tags/test_unit_projects_tags_models.py -v'
```

Expected: all three tests in the file pass.

- [ ] **Step 7: Commit**

```bash
git add api/projects/tags/migrations/0010_add_azure_devops_tag_type.py api/tests/unit/projects/tags/test_unit_projects_tags_models.py
git commit -m "$(cat <<'EOF'
feat(tags): migrate Tag.type for AZURE_DEVOPS choice

Add migration recording AZURE_DEVOPS in the choices list for Tag.type.
No column shape change.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Expected: commit created.

---

## Task 5: Full-suite verification

- [ ] **Step 1: Run linters**

From the `api/` directory:

```bash
make lint
```

Expected: clean. If the linter complains about formatting, run `make lint` again with auto-fix flags per the repo's standard (or check the Makefile target) and re-commit any auto-fixes as a separate commit titled `chore: lint`.

- [ ] **Step 2: Run mypy strict**

```bash
make typecheck
```

Expected: clean. No new `# type: ignore` introduced anywhere.

- [ ] **Step 3: Run the affected test modules end-to-end**

```bash
make test opts='-n0 tests/unit/features/test_unit_feature_external_resources_models.py tests/unit/projects/tags/test_unit_projects_tags_models.py -v'
```

Expected: 7 tests pass (4 from Task 1 + 1 from Task 2 + 2 from Task 3 + 1 from Task 4).

- [ ] **Step 4: Run the broader regression-risk tests**

```bash
make test opts='tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/integrations/gitlab tests/unit/features/test_migrations.py'
```

Expected: all pass. This is the regression guard — we only changed enum values, but we want to confirm the GitLab integration tests and the existing migrations test still work.

- [ ] **Step 5: Confirm clean working tree**

```bash
git status
```

Expected: `nothing to commit, working tree clean`.

- [ ] **Step 6: Confirm the commit graph for this PR**

```bash
git log --oneline feat/azure-devops-spec..HEAD
```

Expected: four commits, in order, with the messages from Tasks 1–4.

---

## Done condition

- 4 commits on `feat/azure-devops-01-resource-types`, branched off `feat/azure-devops-spec`.
- Two enum extensions in code, two migrations recording them.
- 7 new passing tests; no new `# type: ignore`; `make lint`, `make typecheck`, `make test` all clean on the scoped invocations above.
- No `integrations/azure_devops/` directory exists yet — that lands in PR 2.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-spec` (since the spec PR is upstream in the stack). Title: `feat(integrations): add Azure DevOps resource type and tag enums`. Body should link to the spec doc and note this is PR 1 of the stack.

The next plan (`2026-05-28-azure-devops-02-models.md`) will be written after this PR lands.
