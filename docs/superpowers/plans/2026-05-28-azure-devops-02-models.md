# Azure DevOps Integration — PR 2: Models, serializer, configuration viewset

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the `integrations.azure_devops` Django app with two models (`AzureDevOpsConfiguration`, `AzureDevOpsServiceHook`), their migration, a write-only-PAT serializer, a configuration CRUD viewset with structured logging, and URL wiring. After this PR, an authorised user can `POST/GET/PUT/DELETE` an Azure DevOps configuration on a project.

**Architecture:** Mirror the GitLab app's structure (`integrations/gitlab/`) — same `BaseProjectIntegrationModelSerializer` and `ProjectIntegrationBaseViewSet` parents, same write-only PAT masking pattern (`WRITE_ONLY_PLACEHOLDER`), same per-project OneToOne configuration shape. ADO-specific shape: `organisation_url` (cloud or on-prem), `personal_access_token`, and two capability toggles (`labeling_enabled`, `tagging_enabled`). A second model `AzureDevOpsServiceHook` is added now for future use by the inbound webhook (PR 10+), so the migration history doesn't churn later.

**Tech Stack:** Django 5.x, DRF, `softdelete` (via `SoftDeleteExportableModel`), pytest with `pytest-django` + `pytest-structlog`, `responses` for mocking (added in PR 3; not used here), mypy strict.

**Spec reference:** `docs/superpowers/specs/2026-05-28-azure-devops-integration-design.md` — sections "Data model" and "Components → `views/configuration.py`".

**Plan reference (this PR's parent):** `docs/superpowers/plans/2026-05-28-azure-devops-01-resource-types.md` — already merged on `feat/azure-devops-01-resource-types`.

**Stack position:** PR 2 of N. Branches off `feat/azure-devops-01-resource-types`. Branch name: `feat/azure-devops-02-models`. Will PR against `feat/azure-devops-01-resource-types` (or `main` once the previous two PRs in the stack land and this is rebased).

---

## Scope deliberately out of PR 2

- The ADO REST client and PAT validation (defer to PR 3). PR 2 persists whatever PAT is posted without validating it against ADO. This matches the existing GitLab integration's behaviour and keeps PR 2 contained.
- Encryption at rest for the PAT field. The spec line "encrypted at rest using the same approach as `GitLabConfiguration.access_token`" was inaccurate — GitLab's token is a plain `CharField(max_length=300)`. PR 2 mirrors that exactly. If real at-rest encryption is added later it should retrofit both integrations together.
- Browse endpoints, comments, labels, tagging, webhooks, dispatcher wiring — all later PRs.

---

## File Structure

- **Create:** `api/integrations/azure_devops/__init__.py` — empty marker.
- **Create:** `api/integrations/azure_devops/apps.py` — `AzureDevOpsIntegrationConfig(AppConfig)`.
- **Create:** `api/integrations/azure_devops/models.py` — `AzureDevOpsConfiguration` and `AzureDevOpsServiceHook` model classes.
- **Create:** `api/integrations/azure_devops/serializers.py` — `AzureDevOpsConfigurationSerializer` with PAT masking on read.
- **Create:** `api/integrations/azure_devops/views/__init__.py` — public exports.
- **Create:** `api/integrations/azure_devops/views/configuration.py` — `AzureDevOpsConfigurationViewSet`.
- **Create:** `api/integrations/azure_devops/migrations/__init__.py` — empty marker.
- **Create:** `api/integrations/azure_devops/migrations/0001_initial.py` — both models in one migration.
- **Modify:** `api/app/settings/common.py:158-160` — register the new app in `INSTALLED_APPS`.
- **Modify:** `api/projects/urls.py:22-27, 74-78` — import and register the new viewset on the project router.
- **Create:** `api/tests/unit/integrations/azure_devops/__init__.py` — empty marker.
- **Create:** `api/tests/unit/integrations/azure_devops/conftest.py` — shared fixtures (`azure_devops_configuration`).
- **Create:** `api/tests/unit/integrations/azure_devops/test_models.py` — model-level tests (unique constraints, soft-delete behaviour, defaults).
- **Create:** `api/tests/unit/integrations/azure_devops/test_configuration.py` — viewset integration tests (create / get / list / update / delete, write-only PAT, structured log events, existing-configuration 400, permission denials).

No other files are touched in this PR.

---

## Pre-flight

- [ ] **Step 0: Confirm working branch**

```bash
cd /Users/asaphkotzin/Dev/flagsmith
git status
git log --oneline -3
```

Expected: branch is `feat/azure-devops-02-models`, HEAD is `ca2bc76fd` (`style(tests): split the last remaining combined GWT marker`), working tree clean. If the branch does not exist, create it off `feat/azure-devops-01-resource-types`:

```bash
git checkout feat/azure-devops-01-resource-types
git checkout -b feat/azure-devops-02-models
```

---

## Task 1: Scaffold the Django app and register it

**Files:**
- Create: `api/integrations/azure_devops/__init__.py`
- Create: `api/integrations/azure_devops/apps.py`
- Create: `api/integrations/azure_devops/migrations/__init__.py`
- Create: `api/tests/unit/integrations/azure_devops/__init__.py`
- Modify: `api/app/settings/common.py:158-160`
- Test: a single integration test that simply imports the app config

- [ ] **Step 1: Create the empty `__init__.py` files**

```bash
mkdir -p api/integrations/azure_devops/migrations api/tests/unit/integrations/azure_devops
```

Create `api/integrations/azure_devops/__init__.py` with contents:

```python
```

(empty file)

Create `api/integrations/azure_devops/migrations/__init__.py` with contents:

```python
```

(empty file)

Create `api/tests/unit/integrations/azure_devops/__init__.py` with contents:

```python
```

(empty file)

- [ ] **Step 2: Create the `AppConfig`**

Create `api/integrations/azure_devops/apps.py` with the following exact contents:

```python
from django.apps import AppConfig


class AzureDevOpsIntegrationConfig(AppConfig):
    name = "integrations.azure_devops"
```

- [ ] **Step 3: Register the app in `INSTALLED_APPS`**

In `api/app/settings/common.py`, locate the integrations block (currently around line 144-161). Find the line:

```python
    "integrations.gitlab",
```

Add `"integrations.azure_devops",` on the line immediately after:

```python
    "integrations.gitlab",
    "integrations.azure_devops",
    "integrations.grafana",
```

- [ ] **Step 4: Write the smoke test**

Create `api/tests/unit/integrations/azure_devops/test_apps.py` with:

```python
from django.apps import apps


def test_azure_devops_app__django_registry__contains_config() -> None:
    # Given
    app_label = "azure_devops"

    # When
    config = apps.get_app_config(app_label)

    # Then
    assert config.name == "integrations.azure_devops"
```

- [ ] **Step 5: Run the test to verify it passes**

From the `api/` directory:

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_apps.py -v'
```

Expected: 1 passed.

- [ ] **Step 6: Run mypy**

```bash
make typecheck
```

Expected: `Success: no issues found`.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/__init__.py api/integrations/azure_devops/apps.py api/integrations/azure_devops/migrations/__init__.py api/tests/unit/integrations/azure_devops/__init__.py api/tests/unit/integrations/azure_devops/test_apps.py api/app/settings/common.py
git commit -m "$(cat <<'EOF'
feat(integrations): scaffold the integrations.azure_devops Django app

Add an empty app skeleton (apps.py + __init__ + migrations/__init__) and
register it in INSTALLED_APPS so subsequent commits in this PR can add
models, serializers, views, and migrations. No behaviour yet.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: `AzureDevOpsConfiguration` model

**Files:**
- Create: `api/integrations/azure_devops/models.py` (new)
- Create: `api/tests/unit/integrations/azure_devops/conftest.py` (new — fixtures)
- Create: `api/tests/unit/integrations/azure_devops/test_models.py` (new)

- [ ] **Step 1: Write the failing tests**

Create `api/tests/unit/integrations/azure_devops/conftest.py` with the following exact contents:

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

Create `api/tests/unit/integrations/azure_devops/test_models.py` with the following exact contents:

```python
import pytest
from django.db.utils import IntegrityError

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@pytest.mark.django_db
def test_azure_devops_configuration__defaults__has_expected_defaults(
    project: Project,
) -> None:
    # Given
    config = AzureDevOpsConfiguration.objects.create(
        project=project,
        organisation_url="https://dev.azure.com/test-org",
        personal_access_token="ado-test-token",
    )

    # When
    config.refresh_from_db()

    # Then
    assert config.labeling_enabled is False
    assert config.tagging_enabled is False
    assert config.organisation_url == "https://dev.azure.com/test-org"
    assert config.personal_access_token == "ado-test-token"


@pytest.mark.django_db
def test_azure_devops_configuration__second_for_same_project__raises_integrity_error(
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    duplicate_kwargs = {
        "project": project,
        "organisation_url": "https://dev.azure.com/other",
        "personal_access_token": "ado-other",
    }

    # When / Then
    with pytest.raises(IntegrityError):
        AzureDevOpsConfiguration.objects.create(**duplicate_kwargs)


@pytest.mark.django_db
def test_azure_devops_configuration__soft_deleted__allows_recreation(
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    azure_devops_configuration.delete()

    # When
    new_config = AzureDevOpsConfiguration.objects.create(
        project=project,
        organisation_url="https://dev.azure.com/recreated",
        personal_access_token="ado-recreated-token",
    )

    # Then
    assert new_config.pk != azure_devops_configuration.pk
    assert new_config.organisation_url == "https://dev.azure.com/recreated"
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_models.py -v'
```

Expected: collection-time failure — `ModuleNotFoundError: No module named 'integrations.azure_devops.models'` (the file does not exist yet).

- [ ] **Step 3: Create the model**

Create `api/integrations/azure_devops/models.py` with the following exact contents:

```python
from django.db import models

from core.models import SoftDeleteExportableModel


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

(The model intentionally mirrors `GitLabConfiguration` in scope and storage style. The `personal_access_token` is stored as a plain `CharField` — matching `GitLabConfiguration.access_token`'s shape. API-level masking lands in Task 3.)

- [ ] **Step 4: Generate the migration**

```bash
cd api && make docker-up
make django-make-migrations opts='azure_devops --name initial'
```

This produces `api/integrations/azure_devops/migrations/0001_initial.py`. Django picks the name from the `--name` flag, satisfying AGENTS.md's "no auto-generated migration names" rule. Inspect the generated file — it must contain only the `AzureDevOpsConfiguration` `CreateModel` plus standard `SoftDeleteExportableModel` fields (`id`, `deleted_at`, `uuid`). If anything else appears, stop and report NEEDS_CONTEXT.

- [ ] **Step 5: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_models.py -v'
```

Expected: 3 passed.

- [ ] **Step 6: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/models.py api/integrations/azure_devops/migrations/0001_initial.py api/tests/unit/integrations/azure_devops/conftest.py api/tests/unit/integrations/azure_devops/test_models.py
git commit -m "$(cat <<'EOF'
feat(integrations): add AzureDevOpsConfiguration model

One-per-project soft-deletable model storing the organisation URL, the
PAT, and the two capability toggles (labeling_enabled / tagging_enabled).
Mirrors GitLabConfiguration's shape. PAT API masking lands in the next
commit; remote validation against ADO is deferred to PR 3.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: `AzureDevOpsServiceHook` model

**Files:**
- Modify: `api/integrations/azure_devops/models.py` (append the new model)
- Modify: `api/tests/unit/integrations/azure_devops/test_models.py` (append tests)

This model belongs in the same migration if Django will write a fresh `0002_*` for it; we squash by re-generating `0001_initial.py` after Task 2 if practical, otherwise we accept a `0002_add_servicehook.py` and the migrations stay separate (per AGENTS.md "squash newly added migrations whenever you can"). Both outcomes are acceptable; the squash path is preferred.

- [ ] **Step 1: Write the failing tests**

Append to `api/tests/unit/integrations/azure_devops/test_models.py`:

```python
import uuid

from integrations.azure_devops.models import AzureDevOpsServiceHook


@pytest.mark.django_db
def test_azure_devops_service_hook__create__persists_fields(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    ado_project_id = uuid.uuid4()

    # When
    hook = AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="My ADO Project",
        event_type="git.pullrequest.merged",
        subscription_id=uuid.uuid4(),
        secret="rotation-pad-32-bytes-of-urlsafe-junk",
    )

    # Then
    assert hook.configuration == azure_devops_configuration
    assert hook.ado_project_id == ado_project_id
    assert hook.event_type == "git.pullrequest.merged"
    assert hook.uuid is not None


@pytest.mark.django_db
def test_azure_devops_service_hook__duplicate_event__raises_integrity_error(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    ado_project_id = uuid.uuid4()
    AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="Project",
        event_type="git.pullrequest.merged",
        subscription_id=uuid.uuid4(),
        secret="secret-a",
    )

    # When / Then — same (config, ado_project_id, event_type) tuple
    with pytest.raises(IntegrityError):
        AzureDevOpsServiceHook.objects.create(
            configuration=azure_devops_configuration,
            ado_project_id=ado_project_id,
            ado_project_name="Project",
            event_type="git.pullrequest.merged",
            subscription_id=uuid.uuid4(),
            secret="secret-b",
        )


@pytest.mark.django_db
def test_azure_devops_service_hook__different_event__allowed(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    ado_project_id = uuid.uuid4()
    AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="Project",
        event_type="git.pullrequest.merged",
        subscription_id=uuid.uuid4(),
        secret="s1",
    )

    # When
    second = AzureDevOpsServiceHook.objects.create(
        configuration=azure_devops_configuration,
        ado_project_id=ado_project_id,
        ado_project_name="Project",
        event_type="workitem.updated",
        subscription_id=uuid.uuid4(),
        secret="s2",
    )

    # Then
    assert second.event_type == "workitem.updated"
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_models.py -v'
```

Expected: collection or test-time failure — `AzureDevOpsServiceHook` not defined.

- [ ] **Step 3: Append the model**

Append to `api/integrations/azure_devops/models.py`:

```python
import uuid

from django.db import models


class AzureDevOpsServiceHook(SoftDeleteExportableModel):
    configuration = models.ForeignKey(
        "azure_devops.AzureDevOpsConfiguration",
        on_delete=models.CASCADE,
        related_name="service_hooks",
    )
    ado_project_id = models.UUIDField()
    ado_project_name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=64)
    subscription_id = models.UUIDField()
    secret = models.CharField(max_length=128)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["configuration", "ado_project_id", "event_type"],
                name="unique_azure_devops_service_hook_per_event",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]
        indexes = [
            models.Index(fields=["uuid"]),
        ]
```

(The `uuid` import goes at the top of the file alongside the existing `from django.db import models` import; the duplicate `import uuid / from django.db import models` block above is shown inline for clarity — when applying, move both to the file's import block.)

- [ ] **Step 4: Regenerate / extend the migration**

Inspect `api/integrations/azure_devops/migrations/0001_initial.py`. If practical, **squash** the new model into the existing `0001_initial.py` (recommended by AGENTS.md). The simplest path:

```bash
rm api/integrations/azure_devops/migrations/0001_initial.py
make django-make-migrations opts='azure_devops --name initial'
```

This regenerates `0001_initial.py` containing both models. Re-inspect the file. If `makemigrations` instead writes a `0002_*` (e.g. because squashing isn't possible for some reason), accept that and rename it explicitly to `0002_add_service_hook.py`:

```bash
mv api/integrations/azure_devops/migrations/0002_*.py api/integrations/azure_devops/migrations/0002_add_service_hook.py
```

Verify the migration matches Django's expectation:

```bash
make django-make-migrations opts='--check --dry-run azure_devops'
```

Expected: `No changes detected in app 'azure_devops'`.

- [ ] **Step 5: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_models.py -v'
```

Expected: 6 passed (3 from Task 2 + 3 new).

- [ ] **Step 6: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/models.py api/integrations/azure_devops/migrations/ api/tests/unit/integrations/azure_devops/test_models.py
git commit -m "$(cat <<'EOF'
feat(integrations): add AzureDevOpsServiceHook model

Persist one row per (ADO project, event type) we subscribe to on the ADO
side. Unlike GitLab, ADO service hooks are one subscription per event
type, so the unique constraint is on (configuration, ado_project_id,
event_type). The model is added now so the migration history doesn't
churn when the webhook handler lands in a later PR.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Serializer with write-only PAT

**Files:**
- Create: `api/integrations/azure_devops/serializers.py`
- Create: `api/tests/unit/integrations/azure_devops/test_serializers.py`

- [ ] **Step 1: Write the failing test**

Create `api/tests/unit/integrations/azure_devops/test_serializers.py` with:

```python
import pytest

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    WRITE_ONLY_PLACEHOLDER,
    AzureDevOpsConfigurationSerializer,
)


@pytest.mark.django_db
def test_serializer__to_representation__masks_personal_access_token(
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    serializer = AzureDevOpsConfigurationSerializer(instance=azure_devops_configuration)

    # When
    data = serializer.data

    # Then
    assert data["personal_access_token"] == WRITE_ONLY_PLACEHOLDER
    assert data["organisation_url"] == azure_devops_configuration.organisation_url
    assert data["labeling_enabled"] is False
    assert data["tagging_enabled"] is False
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py -v'
```

Expected: import error — `integrations.azure_devops.serializers` does not exist yet.

- [ ] **Step 3: Create the serializer**

Create `api/integrations/azure_devops/serializers.py` with the following exact contents:

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

- [ ] **Step 4: Run the test to verify it passes**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_serializers.py -v'
```

Expected: 1 passed.

- [ ] **Step 5: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add api/integrations/azure_devops/serializers.py api/tests/unit/integrations/azure_devops/test_serializers.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps configuration serializer

DRF ModelSerializer mirroring GitLab's pattern: PAT is writeable on
input but masked with the WRITE_ONLY_PLACEHOLDER on output. Uses
BaseProjectIntegrationModelSerializer so the project-scoped one-to-one
soft-delete recreate logic comes for free.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Viewset, URL wiring, integration tests

**Files:**
- Create: `api/integrations/azure_devops/views/__init__.py`
- Create: `api/integrations/azure_devops/views/configuration.py`
- Modify: `api/projects/urls.py` (import + router registration)
- Create: `api/tests/unit/integrations/azure_devops/test_configuration.py`

- [ ] **Step 1: Write the failing integration tests**

Create `api/tests/unit/integrations/azure_devops/test_configuration.py` with:

```python
import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


def test_create_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-test-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["personal_access_token"] == "write-only"
    assert response.json()["labeling_enabled"] is False
    assert response.json()["tagging_enabled"] is False

    config = AzureDevOpsConfiguration.objects.get(project=project)
    assert config.organisation_url == "https://dev.azure.com/test-org"
    assert config.personal_access_token == "ado-test-token"

    assert log.events == [
        {
            "event": "configuration.created",
            "level": "info",
            "organisation__id": project.organisation_id,
            "project__id": project.id,
            "ado__organisation__url": "https://dev.azure.com/test-org",
        },
    ]


def test_create_configuration__already_exists__returns_400(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/other",
        "personal_access_token": "ado-other-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_list_configuration__existing__returns_masked_representation(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["personal_access_token"] == "write-only"
    assert rows[0]["organisation_url"] == azure_devops_configuration.organisation_url


def test_update_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
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

    # When
    response = admin_client_new.put(detail_url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["personal_access_token"] == "write-only"

    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.organisation_url == "https://dev.azure.com/updated"
    assert azure_devops_configuration.personal_access_token == "ado-updated-token"
    assert azure_devops_configuration.labeling_enabled is True
    assert azure_devops_configuration.tagging_enabled is True

    assert log.events == [
        {
            "event": "configuration.updated",
            "level": "info",
            "organisation__id": project.organisation_id,
            "project__id": project.id,
            "ado__organisation__url": "https://dev.azure.com/updated",
        },
    ]


def test_delete_configuration__existing__soft_deletes_and_logs(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )

    # When
    response = admin_client_new.delete(detail_url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not AzureDevOpsConfiguration.objects.filter(project=project).exists()
    assert AzureDevOpsConfiguration.objects.all_with_deleted().filter(project=project).exists()

    assert log.events == [
        {
            "event": "configuration.deleted",
            "level": "info",
            "organisation__id": project.organisation_id,
            "project__id": project.id,
        },
    ]


def test_list_configuration__unauthenticated__returns_401(
    api_client: APIClient,
    project: Project,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
```

The `admin_client_new`, `api_client`, `project`, and `log` fixtures are already provided by the project's root `conftest.py` and `pytest-structlog`. The `azure_devops_configuration` fixture lives in the local `conftest.py` from Task 2.

- [ ] **Step 2: Run the tests to verify they fail**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_configuration.py -v'
```

Expected: failures — either import errors (`integrations.azure_devops.views` not found) or 404 on the URL.

- [ ] **Step 3: Create the views package**

Create `api/integrations/azure_devops/views/__init__.py` with:

```python
from integrations.azure_devops.views.configuration import (
    AzureDevOpsConfigurationViewSet,
)

__all__ = ["AzureDevOpsConfigurationViewSet"]
```

Create `api/integrations/azure_devops/views/configuration.py` with:

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
            project__id=config.project_id,
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

- [ ] **Step 4: Wire URLs**

In `api/projects/urls.py`, find the import block around line 22-27:

```python
from integrations.gitlab.views import (
    BrowseGitLabIssues,
    BrowseGitLabMergeRequests,
    BrowseGitLabProjects,
    GitLabConfigurationViewSet,
)
```

Add directly after it:

```python
from integrations.azure_devops.views import AzureDevOpsConfigurationViewSet
```

Then find the GitLab router registration around line 74-78:

```python
projects_router.register(
    r"integrations/gitlab",
    GitLabConfigurationViewSet,
    basename="integrations-gitlab",
)
```

Add directly after it (before the `grafana` registration on line 79):

```python
projects_router.register(
    r"integrations/azure-devops",
    AzureDevOpsConfigurationViewSet,
    basename="integrations-azure-devops",
)
```

- [ ] **Step 5: Run the tests**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/test_configuration.py -v'
```

Expected: 6 passed.

- [ ] **Step 6: Run mypy**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 7: Commit**

```bash
git add api/integrations/azure_devops/views/ api/projects/urls.py api/tests/unit/integrations/azure_devops/test_configuration.py
git commit -m "$(cat <<'EOF'
feat(integrations): add Azure DevOps configuration viewset and URL wiring

CRUD viewset under /api/v1/projects/{id}/integrations/azure-devops/
following the GitLab pattern: BaseProjectIntegrationBaseViewSet for the
permission and one-config-per-project semantics, structured logging on
create / update / delete via the "azure_devops" structlog logger,
write-only PAT masking via the serializer. Remote validation against
ADO is deferred to PR 3 when the REST client lands.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Full-suite verification

- [ ] **Step 1: Lint**

```bash
make lint
```

Expected: clean. If ruff auto-fixes anything, accept and amend the relevant Task commit (or add a `style:` commit at the end if the change spans several files).

- [ ] **Step 2: Type check**

```bash
make typecheck
```

Expected: clean.

- [ ] **Step 3: Run the full new test directory**

```bash
make test opts='-n0 tests/unit/integrations/azure_devops/ -v'
```

Expected: ~11 passed (1 app smoke + 6 model tests + 1 serializer test + 6 viewset tests minus any overlap; the implementer may end up at a slightly different total depending on test groupings).

- [ ] **Step 4: Regression guard — adjacent integration tests**

```bash
make test opts='tests/unit/integrations/gitlab tests/unit/integrations/github tests/unit/features/test_unit_feature_external_resources_views.py tests/unit/features/test_migrations.py'
```

Expected: all pass. Confirms the new app's INSTALLED_APPS registration and URL addition didn't break adjacent integrations.

- [ ] **Step 5: Migration consistency**

```bash
make django-make-migrations opts='--check --dry-run azure_devops feature_external_resources tags'
```

Expected: `No changes detected` across all three apps.

- [ ] **Step 6: Verify branch state**

```bash
git status
git log --oneline feat/azure-devops-01-resource-types..HEAD
```

Expected: working tree clean; five commits on this branch (Task 1-5 each producing one commit).

---

## Done condition

- Five feature commits on `feat/azure-devops-02-models` (plus any optional `style:` commit) producing a working `AzureDevOpsConfiguration` CRUD endpoint under `/api/v1/projects/{id}/integrations/azure-devops/`.
- Two models, one migration, one serializer, one viewset, two view files, URL wiring.
- All new tests pass; mypy strict, ruff, and `flagsmith-lint-tests` clean.
- Migration consistency: `--check --dry-run` reports no drift for any app.

When all boxes are ticked, push the branch and open the PR against `feat/azure-devops-01-resource-types` (stacked). Title: `feat(integrations): Azure DevOps models, serializer, configuration viewset (PR 2/N)`. The body should link to the spec, the PR-2 plan, and the parent PR.

The next plan (`2026-05-28-azure-devops-03-client.md`) will be written after this PR lands — it'll add the ADO REST client, typed exceptions, and wire PAT validation into the viewset.
