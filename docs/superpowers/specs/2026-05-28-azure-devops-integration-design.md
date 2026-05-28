# Azure DevOps integration — design

**Status:** Draft for implementation
**Date:** 2026-05-28
**Author:** Asaph Kotzin (with Claude)

## Summary

Add a single in-repo Flagsmith integration for Azure DevOps that links Azure
Repos pull requests and Azure Boards work items to Flagsmith features as
`FeatureExternalResource` rows. The integration follows the GitLab pattern
(newer and cleaner of the two existing VCS integrations), shares one
configuration per Flagsmith project across Repos and Boards capabilities, and
supports both Azure DevOps cloud (`dev.azure.com`) and Azure DevOps Server
(on-prem). v1 is gated behind a Flagsmith-on-Flagsmith feature flag.

This spec deliberately does **not** introduce a Marketplace extension (the
shape of the existing Jira integration). The Jira "integration" in this
repository is only a docs page; the actual extension lives outside the
codebase. An Azure DevOps Marketplace extension can be a follow-up project; it
does not block or depend on this work.

## Goals

- Users can configure one Azure DevOps connection per Flagsmith project
  (organisation URL + PAT) and toggle Repos / Boards capabilities on that one
  configuration.
- Users can link Azure pull requests and Azure work items to features through
  a typeahead picker that browses ADO projects, repositories, PRs, and work
  items.
- Linking, unlinking, and Flagsmith-side feature-state changes post comments
  back to the linked ADO resource.
- Linking optionally applies a `flagsmith` tag on the ADO PR or work item.
- Linked features carry Flagsmith system tags that reflect ADO state
  (PR open/merged/draft, work item open/closed).
- ADO service hooks keep those system tags fresh: when a PR merges or a work
  item closes in ADO, the Flagsmith tag updates automatically.
- v1 covers ADO cloud and Azure DevOps Server with PAT authentication.

## Non-goals

- Microsoft Entra OAuth (PAT only in v1).
- Azure DevOps Marketplace extension (separate, future project).
- WIQL / saved-query-driven work-item search (basic title + state + type only).
- Cross-organisation linking from one Flagsmith project (mirrors GitLab's
  single-instance constraint).
- E2E (Playwright) tests against a live ADO test organisation.
- Refactoring `integrations/vcs/` into a true provider abstraction. Deferred
  until three concrete providers (GitHub, GitLab, Azure) exist, at which
  point the right abstraction will be clearer.

## Architecture

A new Django app `api/integrations/azure_devops/` lives alongside `github/`
and `gitlab/` and follows the GitLab layout: `client/`, `services/`,
`views/`, `models.py`, `serializers.py`, `mappers.py`, `tasks.py`,
`types.py`, `metrics.py`, `templates/azure_devops/`.

Two new values are added to
`features.feature_external_resources.models.ResourceType`:

- `AZURE_DEVOPS_PULL_REQUEST`
- `AZURE_DEVOPS_WORK_ITEM`

plus a module-level tuple `AZURE_DEVOPS_RESOURCE_TYPES` mirroring
`GITLAB_RESOURCE_TYPES`. The existing dispatcher in
`api/integrations/vcs/services.py` gains a parallel
`if resource.type in AZURE_DEVOPS_RESOURCE_TYPES:` branch alongside the GitLab
branch. The GitHub and GitLab integrations are not otherwise modified.

The whole integration is gated by a Flagsmith-on-Flagsmith boolean flag
`azure_devops_integration`, default `false`, evaluated with
`organisation.openfeature_evaluation_context`
(`api/organisations/models.py:126`). When the flag resolves to `false`, the
configuration viewset 404s, the dispatcher branch short-circuits, and the
frontend integration card is hidden.

## Data model

### `AzureDevOpsConfiguration`

`integrations.azure_devops.models.AzureDevOpsConfiguration(SoftDeleteExportableModel)`

| Field                    | Type / notes                                                                 |
|--------------------------|------------------------------------------------------------------------------|
| `project`                | `OneToOneField("projects.Project", on_delete=CASCADE, related_name="azure_devops_config")` |
| `organisation_url`       | `URLField(max_length=300)` — normalised on save: trailing slash stripped     |
| `personal_access_token`  | `CharField(max_length=300)` — write-only on the API; encrypted at rest using the same approach as `GitLabConfiguration.access_token` |
| `labeling_enabled`       | `BooleanField(default=False)` — when true, adds a `flagsmith` tag to the ADO PR / work item on link |
| `tagging_enabled`        | `BooleanField(default=False)` — when true, applies Flagsmith system tags to the feature reflecting ADO state |

`organisation_url` accepts ADO cloud shapes (`https://dev.azure.com/{org}`)
and Azure DevOps Server shapes (`https://{host}/{collection}`). Validation
short-circuits with a clear error if the URL cannot be reduced to one of
these.

### `AzureDevOpsServiceHook`

`integrations.azure_devops.models.AzureDevOpsServiceHook(SoftDeleteExportableModel)`

| Field              | Type / notes                                                            |
|--------------------|-------------------------------------------------------------------------|
| `configuration`    | `ForeignKey(AzureDevOpsConfiguration, on_delete=CASCADE, related_name="service_hooks")` |
| `ado_project_id`   | `UUIDField` — ADO project GUID (ADO projects are identified by GUID; unlike GitLab there is no human-readable path identifier of equal authority) |
| `ado_project_name` | `CharField(max_length=200)` — denormalised for display and URL parsing  |
| `event_type`       | `CharField(max_length=64)` — one of `git.pullrequest.merged`, `git.pullrequest.updated`, `workitem.updated` |
| `subscription_id`  | `UUIDField` — returned by ADO on subscription create                    |
| `secret`           | `CharField(max_length=128)` — the password we send to ADO in the hook URL's basic-auth header |
| `uuid`             | `UUIDField(default=uuid4)` — our path identifier on the inbound webhook URL |
| `created_at`       | `DateTimeField(auto_now_add=True)`                                      |

Unique constraint on `(configuration, ado_project_id, event_type)` filtered
to `deleted_at__isnull=True`. Index on `uuid` for the webhook lookup.

Note: ADO service hooks are **one subscription per event type** (unlike
GitLab's one-hook-many-events model), so the table contains one row per
(ADO project × event type) we care about.

### `FeatureExternalResource` (existing model, extended)

`ResourceType` gains:

```python
AZURE_DEVOPS_PULL_REQUEST = "AZURE_DEVOPS_PULL_REQUEST", "Azure DevOps Pull Request"
AZURE_DEVOPS_WORK_ITEM    = "AZURE_DEVOPS_WORK_ITEM",    "Azure DevOps Work Item"
```

and a module-level tuple `AZURE_DEVOPS_RESOURCE_TYPES = (ResourceType.AZURE_DEVOPS_PULL_REQUEST, ResourceType.AZURE_DEVOPS_WORK_ITEM)`.

The `metadata` JSON for ADO resources matches the `AzureDevOpsResourceMetadata`
TypedDict declared in `azure_devops.client.types`:

```python
class AzureDevOpsResourceMetadata(TypedDict, total=False):
    title: str
    state: str            # PR: "active"|"completed"|"abandoned"; work item: "Active"|"Resolved"|"Closed"|...
    work_item_type: str   # work-item only: "Bug"|"Task"|"User Story"|"Feature"|"Epic"
    is_draft: bool        # PR only
```

`metadata` is updated in place by the webhook handler when state changes
upstream.

### Flagsmith system tags

When `tagging_enabled` is true, links and webhook state updates apply Flagsmith
project tags from the following set, all created lazily with
`Tag.objects.get_or_create(..., is_system_tag=True, type=TagType.AZURE_DEVOPS.value)`:

- `PR Open`
- `PR Merged`
- `PR Abandoned`
- `PR Draft`
- `Work Item Open`
- `Work Item Closed`

Labels deliberately omit the "Azure DevOps" prefix to match the brevity
convention the GitLab tags follow (`Issue Open`, `MR Merged`). The
`TagType.AZURE_DEVOPS` enum value scopes them at the type layer, and
"PR" / "Work Item" already disambiguate from GitLab's "MR" / "Issue".

A new `TagType.AZURE_DEVOPS` value is added to
`projects.tags.models.TagType` (mirroring `TagType.GITHUB`). Tag colour is
declared as an `AZURE_DEVOPS_TAG_COLOR` constant under
`integrations.azure_devops.constants`.

## Components

### `client/api.py`

Thin `requests`-based wrapper around the ADO REST API v7. All functions accept
`organisation_url` and `pat` explicitly and use HTTP Basic auth with empty
username (the ADO PAT convention).

- `list_projects(organisation_url, pat, *, continuation_token=None, top=100) -> AdoProjectsPage`
- `list_repositories(organisation_url, pat, ado_project_id) -> list[AdoRepository]`
- `list_pull_requests(organisation_url, pat, ado_project_id, *, search_text=None, state=None, continuation_token=None, top=100) -> AdoPullRequestsPage`
- `list_work_items(organisation_url, pat, ado_project_id, *, search_text=None, state=None, work_item_type=None, continuation_token=None, top=100) -> AdoWorkItemsPage` — internally executes a WIQL `POST /wiql` then `GET /workitemsbatch` to hydrate fields. Continuation is emulated by offsetting into the WIQL id list.
- `create_pull_request_thread(organisation_url, pat, repository_id, pull_request_id, body)`
- `add_work_item_comment(organisation_url, pat, ado_project_id, work_item_id, body)`
- `add_tag_to_pull_request(...)` / `remove_tag_from_pull_request(...)`
- `add_tag_to_work_item(...)` / `remove_tag_from_work_item(...)`
- `create_subscription(organisation_url, pat, *, ado_project_id, event_type, hook_url, basic_auth_password) -> AdoSubscription`
- `delete_subscription(organisation_url, pat, subscription_id)`

ADO 401/403 raise a typed `AzureDevOpsAuthError`. 404 on a single-resource
lookup raises `AzureDevOpsNotFoundError`. Network and 5xx errors bubble up as
`requests.RequestException` (the comment/label task layer catches these). 409
on `create_subscription` is caught and the existing subscription adopted
(idempotent registration).

### `client/types.py`

TypedDicts for ADO REST responses: `AdoProject`, `AdoRepository`,
`AdoPullRequest`, `AdoWorkItem`, `AdoSubscription`, plus the page-shape
wrappers used by the browse client functions. Plus `AzureDevOpsResourceMetadata`
(see Data model).

### `services/url_parsing.py`

- `parse_pull_request_url(url) -> AdoPullRequestRef | None` where `AdoPullRequestRef = (organisation_root, project, repository, pr_id)`
- `parse_work_item_url(url) -> AdoWorkItemRef | None` where `AdoWorkItemRef = (organisation_root, project, work_item_id)`

Both support the cloud shape
`https://dev.azure.com/{org}/{project}/_git/{repo}/pullrequest/{id}` /
`.../_workitems/edit/{id}` and the on-prem shape
`https://{host}/{collection}/{project}/_git/{repo}/pullrequest/{id}` /
`.../_workitems/edit/{id}`. Returns `None` for any URL that does not match —
parsing never raises. Callers short-circuit on `None`.

### `services/comments.py`

Templates rendered from `templates/azure_devops/*.md` using the same context
shape as GitLab. The template files added under
`integrations/azure_devops/templates/azure_devops/`:

- `feature_linked_comment.md`
- `feature_unlinked_comment.md`
- `feature_state_changed_comment.md`
- `feature_deleted_comment.md`

Functions:

- `post_linked_comment(resource: FeatureExternalResource) -> None`
- `post_unlinked_comment(feature_name, feature_id, resource_url, resource_type, project_id) -> None`
- `post_feature_deleted_comment(feature_name, feature_id, project_id) -> None`
- `post_state_change_comment(feature_state: FeatureState) -> None`
- `post_azure_devops_state_change_comment_for_feature_state(feature_state)` — the entry point called from the existing `FeatureState` save path, no-ops when the project has no `azure_devops_config`.

Each post goes through an internal `_post_to_resource` helper that selects
the right ADO endpoint based on resource type. `requests.RequestException`
is caught and logged as `comment.post_failed`; the user-facing action that
triggered the comment still succeeds.

### `services/tagging.py`

- `apply_initial_tag(resource: FeatureExternalResource) -> None` — applies the
  system tag implied by `resource.metadata` (and `tagging_enabled`).
- `clear_tag_for_resource(resource: FeatureExternalResource) -> None` — removes
  any Azure system tag the feature carries solely because of this resource.
- `refresh_tags_for_resource(resource: FeatureExternalResource) -> None` —
  called from the inbound webhook handler when `metadata.state` changes.

### `services/labels.py`

- `apply_label_to_pull_request` / `apply_label_to_work_item`
- `remove_label_from_pull_request` / `remove_label_from_work_item`

Adds a `flagsmith` tag on the ADO resource when `labeling_enabled`. ADO calls
these "tags"; we keep "label" in code to match GitLab naming. 404 / 409 are
swallowed idempotently.

### `services/webhooks.py`

- `register_subscriptions_for_resource(resource, *, api_base_url)` —
  parses `resource.url` to obtain the ADO project **name** (URLs contain the
  name, not the GUID), then resolves the GUID via the client's
  `list_projects` lookup (cached per request), then calls
  `ensure_subscriptions_registered` with both the GUID and the name. The
  name → GUID translation is the only place this resolution happens; every
  downstream service takes `ado_project_id` as a GUID.
- `ensure_subscriptions_registered(config, ado_project_id, ado_project_name, *, api_base_url)` —
  no-ops if all three event types already have a live row; otherwise
  creates the missing subscriptions via ADO API and persists rows. Per-hook
  secret is `secrets.token_urlsafe(32)`. UUID-based hook URL:
  `urljoin(api_base_url, f"/api/v1/azure-devops-webhook/{uuid}/")`.
- `deregister_subscriptions_for_resource(resource)` — calls
  `deregister_subscriptions_for_project` if no live resources remain.
- `deregister_subscriptions_for_project(config, ado_project_id)` — deletes
  all three subscriptions and soft-deletes the local rows. 404 on delete is
  logged as `subscription.already_gone` and the row is removed anyway.
- `has_live_resource_for_project(config, ado_project_id) -> bool` — mirrors
  GitLab's `has_live_resource_for_path`.

### `views/configuration.py`

CRUD viewset for `AzureDevOpsConfiguration` (one per project). Permission
class checks `MANAGE_PROJECT` on the parent project. On create / update,
the viewset issues a `GET _apis/projects?$top=1` against the supplied URL
and PAT and returns `400` with a clear message if ADO rejects the credentials.
PAT is write-only via a `WRITE_ONLY_PLACEHOLDER` pattern (matches GitLab).

### `views/browse_azure_devops.py`

Read-only, paginated, all scoped to a Flagsmith project that has an
`AzureDevOpsConfiguration`:

- `GET /projects/{flagsmith_project_id}/integrations/azure-devops/ado-projects?page=...&page_size=...`
- `GET /projects/{flagsmith_project_id}/integrations/azure-devops/repositories?ado_project_id=...`
- `GET /projects/{flagsmith_project_id}/integrations/azure-devops/pull-requests?ado_project_id=...&search_text=...&state=...`
- `GET /projects/{flagsmith_project_id}/integrations/azure-devops/work-items?ado_project_id=...&search_text=...&state=...&work_item_type=...`

Pagination is by continuation token, surfaced to clients as a `next_page`
cursor. ADO 4xx is surfaced to the frontend as a structured error;
`requests.RequestException` becomes a `502 Bad Gateway` with a `code` field.

### `views/webhook.py`

`POST /api/v1/azure-devops-webhook/{uuid}/`:

1. Look up `AzureDevOpsServiceHook` by `uuid`; `404` if missing or
   soft-deleted.
2. Read the basic-auth password from the request; constant-time compare
   against the row's `secret`. Return `401` on mismatch.
3. Read `eventType` from the JSON body. If it is not one of the three we
   subscribe to, return `200` with no work (we never want ADO to mark our
   endpoint dead).
4. Extract the resource identifiers from the payload — `resource.repository.id`
   + `resource.pullRequestId` for PR events; `resource.id` and the project
   GUID for work item events. Find matching live `FeatureExternalResource`
   rows by parsing each stored URL with `services.url_parsing` and comparing
   the structured tuple (rather than raw string equality, which would break
   on legacy `visualstudio.com` host forms or trailing-slash variance).
   For each match, scoped to the hook's configuration's project:
   - Update `metadata.state` (and `metadata.is_draft` for PRs).
   - Call `tagging.refresh_tags_for_resource(resource)`.
5. Return `200`. Handler is idempotent under replay (same payload posted
   twice yields the same end state, no duplicate work). Verify `ado_project_id`
   on the parsed payload matches the hook's stored value before updating
   anything.

### `tasks.py`

Async wrappers around the comment-posting and webhook-management services,
invoked from the `vcs` dispatcher. Names follow the GitLab pattern:
`apply_azure_devops_label`, `remove_azure_devops_label`,
`post_azure_devops_linked_comment`, `post_azure_devops_unlinked_comment`,
`post_azure_devops_state_change_comment`,
`register_azure_devops_subscriptions`, `deregister_azure_devops_subscriptions`.

### `mappers.py`

ADO REST JSON → our typed dicts for the browse endpoints. Keeps the views
thin and centralises every shape assumption.

### `metrics.py`

Prometheus metrics following the `flagsmith_{domain}_{entity}_{unit}` naming
convention:

- Counter `flagsmith_azure_devops_resource_links_total{resource_type, outcome}`
- Counter `flagsmith_azure_devops_comments_posted_total{resource_type, kind, outcome}` — `kind` ∈ `linked|unlinked|state_change|deleted`
- Counter `flagsmith_azure_devops_api_requests_total{endpoint, status_class}`
- Counter `flagsmith_azure_devops_webhook_events_total{event_type, outcome}`
- Histogram `flagsmith_azure_devops_api_request_duration_seconds{endpoint}`

Each metric has a complete `help` string explaining its meaning per
`AGENTS.md`.

### `vcs/services.py` (modified)

`dispatch_vcs_on_resource_create` and `dispatch_vcs_on_resource_destroy` gain
an `AZURE_DEVOPS_RESOURCE_TYPES` branch with the same shape as the existing GitLab
branch: register subscriptions, apply initial tag synchronously, dispatch
label + linked-comment tasks; on destroy queue the unlinked/label-removal
tasks and clear the tag, then deregister subscriptions if no more live
resources remain under the ADO project.

### Frontend

New TypeScript/React work mirroring the existing GitLab work:

- `frontend/web/components/AzureDevOpsLinkSection.tsx` — settings panel
  rendering the configuration form (organisation URL, PAT, `labeling_enabled`,
  `tagging_enabled`) and a delete affordance.
- `frontend/web/components/AzureDevOpsProjectSelect.tsx` — ADO-project picker
  used by both the PR and the work-item flow.
- `frontend/web/components/AzureDevOpsSearchSelect.tsx` — PR / work-item
  picker. Branches its backing endpoint and the result-row rendering by
  resource type.
- `frontend/common/services/useAzureDevOps.ts` — RTK Query service for the
  browse endpoints.
- `frontend/common/services/useAzureDevOpsConfiguration.ts` — RTK Query
  service for configuration CRUD.
- `frontend/common/types/responses.ts` and `requests.ts` — types for ADO
  configuration, browse responses, and the metadata snapshot the frontend
  attaches on link.
- Integration card added to the integrations index, hidden when the
  `azure_devops_integration` flag is off.

## Data flow

### Link (PR or work item)

1. Frontend picker calls `GET .../work-items?...` (or pull-requests). View
   loads the project's `AzureDevOpsConfiguration`, calls the client with the
   stored PAT, and returns a paginated, mapped result.
2. User selects a resource. Frontend POSTs to the existing
   `FeatureExternalResource` create endpoint with `type=AZURE_DEVOPS_WORK_ITEM` /
   `AZURE_DEVOPS_PULL_REQUEST`, the URL, and the metadata snapshot.
3. The model's `AFTER_SAVE` hook for ADO types calls the `vcs` dispatcher
   create-branch, which:
   - calls `services.webhooks.register_subscriptions_for_resource` —
     idempotent; first link under an ADO project creates the three
     subscriptions, subsequent links no-op.
   - calls `services.tagging.apply_initial_tag` synchronously.
   - queues `apply_azure_devops_label.delay(resource.id)` (only effective
     when `labeling_enabled`).
   - queues `post_azure_devops_linked_comment.delay(resource.id)`.

### Unlink

1. `BEFORE_DELETE` hook on `FeatureExternalResource` fires the dispatcher's
   destroy-branch. The caller-side fields are copied into kwargs because the
   row will be gone by the time the async tasks run.
2. The dispatcher:
   - queues `remove_azure_devops_label.delay(...)` (no-op when
     `labeling_enabled` is false).
   - queues `post_azure_devops_unlinked_comment.delay(...)`.
   - calls `services.tagging.clear_tag_for_resource(resource)` synchronously.
3. After the row is deleted, the unlinked-comment task also calls
   `services.webhooks.has_live_resource_for_project`; if no live resources
   remain under the same `ado_project_id`, it calls
   `deregister_subscriptions_for_project` to clean up the three
   subscriptions.

### State change: Flagsmith → ADO

`post_azure_devops_state_change_comment_for_feature_state(feature_state)` is
added to the call site that already fans out to GitLab. It short-circuits
when the project has no `azure_devops_config`. Otherwise queues
`post_azure_devops_state_change_comment.delay(feature_state.id)`, which
iterates every linked ADO PR and work item under the project and posts a
per-environment state-change comment.

### State change: ADO → Flagsmith

The inbound webhook handler (`views/webhook.py`) updates `metadata.state` in
place and rotates the Flagsmith system tag via
`tagging.refresh_tags_for_resource`. Always returns `200` so ADO does not
mark our endpoint dead. Idempotent under replay.

### Feature deletion

The existing feature-delete path that already calls into GitLab for
deletion comments gains a parallel call into
`integrations.azure_devops.services.comments.post_feature_deleted_comment`.

## Error handling

- **Bad PAT at save time:** `GET _apis/projects?$top=1` validation in the
  configuration view returns `400` with a message identifying the auth
  failure. No partial state is persisted.
- **ADO 401 / 403 at runtime:** logged as `auth.rejected`; the comment /
  label task records the failure and does not retry — a revoked PAT will not
  fix itself. The user-facing action succeeds.
- **ADO 404 on a linked resource:** the PR / work item was deleted upstream.
  Comment tasks log `resource.not_found` and stop. The
  `FeatureExternalResource` is *not* deleted — matches GitLab's behaviour.
- **ADO 5xx / network errors:** logged with `exc_info`; user-facing action
  succeeds. No automatic retry in v1 (matches GitLab).
- **Subscription drift:** 404 on `delete_subscription` is logged as
  `subscription.already_gone` and the local row is removed. 409 on
  `create_subscription` is treated as "subscription already exists" — the
  existing one is looked up and its id stored.
- **Webhook auth failure:** `401` with no detail in the body. Constant-time
  compare against `secret`.
- **Webhook for an event we don't handle:** `200`, no-op.
- **Webhook for a resource that doesn't match any live FER:** `200`, no-op.
- **URL parsing:** never raises — every caller short-circuits on `None`.
- **On-prem `http://` URLs:** logged as a warning at save time; not blocked.

## Security

- PAT stored encrypted at rest using the same approach as
  `GitLabConfiguration.access_token`. Write-only on the API surface via the
  `WRITE_ONLY_PLACEHOLDER` pattern.
- Inbound webhooks authenticated with a per-hook 32-byte URL-safe secret sent
  by ADO as the Basic-auth password (ADO subscription `httpHeaders` input).
  Constant-time compare on receive.
- Webhook handler verifies `ado_project_id` in the payload against the
  matched `AzureDevOpsServiceHook` row before any DB work.
- Outbound calls to `organisation_url` follow the scheme the user provided;
  no automatic upgrade or downgrade. `http://` is permitted (some on-prem
  installs require it) with a logged warning.
- No PII in structured logs — orgs / users referenced by id only.

## Observability

### Structured logs

Logger name: `"azure_devops"`. Event names follow `entity.action` per
`AGENTS.md`. Standard attributes: `organisation__id`, `project__id`,
`feature__id`, `ado__organisation__url`, `ado__project__id`,
`ado__resource__id`, `ado__event__type` where applicable.

Events:

- `resource.linked` / `resource.unlinked`
- `comment.posted` / `comment.post_failed`
- `label.applied` / `label.apply_failed`
- `subscription.registered` / `subscription.deregistered` /
  `subscription.registration_failed` / `subscription.already_gone`
- `webhook.received` / `webhook.rejected` / `webhook.processed`
- `auth.rejected`
- `resource.not_found`

### Metrics

See `metrics.py` in the Components section. Counters cover all the
domain-event moments above; one histogram covers ADO API latency.

## Feature flag and rollout

- Flag key: `azure_devops_integration`. Boolean. Default `false`.
- Evaluated via `client.get_boolean_value("azure_devops_integration", default_value=False, evaluation_context=organisation.openfeature_evaluation_context)` at the request layer and the dispatcher branch.
- Added to the Flagsmith-on-Flagsmith project as part of this work;
  `updateflagsmithenvironment` management command run to refresh the cache.
- Rollout strategy: enable for the Flagsmith team org first, then pilot
  organisations, then ramp to GA. The flag remains in place for the first
  GA release in case a quick disable is needed; cleanup follow-up issue
  filed at GA.

## Testing

Targets the codebase's standing 100% diff-coverage policy.

### Unit tests

Under `api/tests/unit/integrations/azure_devops/`. Fixtures in a local
`conftest.py`: `azure_devops_configuration`, `azure_devops_service_hook`,
`mock_ado_client` (requests-mock based), `azure_pr_external_resource`,
`azure_work_item_external_resource`.

- `test_url_parsing.py` — parametrised cloud / on-prem / malformed URLs,
  collection-vs-org distinction.
- `test_client.py` — basic-auth header shape, WIQL + workitemsbatch
  sequence for `list_work_items`, paging, 401/404/5xx handling.
- `test_services_tagging.py` — system-tag application by state, `tagging_enabled`
  off, refresh on state change.
- `test_services_comments.py` — rendered-template assertions for each
  comment kind; no-config short-circuit.
- `test_services_labels.py` — `labeling_enabled` on/off; 404/409 idempotency.
- `test_services_webhooks.py` — register creates three subscriptions,
  no-ops on second call; deregister removes all three; 404 / 409
  idempotency; `has_live_resource_for_project` true/false.
- `test_models.py` — write-only PAT, unique constraints, soft-delete.
- `test_metrics.py` — counters and histogram fire with the right labels.
- `test_vcs_dispatcher.py` — link / unlink dispatch the expected azure
  side-effects for `AZURE_DEVOPS_*` types; GitLab branch regression guard.

### Integration tests

Under `api/tests/integration/integrations/azure_devops/`. ADO upstream is
requests-mocked.

- `test_configuration_views.py` — CRUD, permission denials, write-only PAT
  round-trip, PAT validation call on save.
- `test_browse_views.py` — each browse endpoint with valid params, missing
  config, ADO 401/403/5xx surface, paging cursor round-trip.
- `test_link_pr.py` / `test_link_work_item.py` — end-to-end link with
  subscriptions registered, Flagsmith tag applied, ADO label applied,
  linked comment posted, structured log events asserted via `caplog`.
- `test_unlink.py` — last-resource case (deregisters subscriptions) and
  has-other-resources case (does not).
- `test_state_change_comment.py` — feature state toggle fans comments out
  to every linked PR and work item.
- `test_webhook.py` — valid / invalid basic-auth, each event type's payload
  shape, idempotent replay, unhandled event type returns 200, mismatched
  `ado_project_id` returns 200 no-op.
- `test_feature_flag_gate.py` — flag off hides card and 404s endpoints;
  flag on activates everything. Uses the existing `mock_openfeature_client`
  fixture.

### Frontend

Jest component tests for the picker and link-section components mirroring
the existing GitLab Jest tests under
`frontend/web/components/__tests__/`. No new Playwright tests in v1 — ADO
E2E needs a stable test org and is documented as a follow-up.

### Type checking

`make typecheck` (mypy strict) passes cleanly. No new `# type: ignore`
introduced; any that are necessary are documented inline per `AGENTS.md`.

## Migrations

Auto-generated via `make docker-up django-make-migrations` with a chosen
name (per `AGENTS.md`, we do not accept auto-generated names). Migrations
added:

- `integrations/azure_devops/0001_initial.py` — creates
  `AzureDevOpsConfiguration` and `AzureDevOpsServiceHook`.
- `features/feature_external_resources/000X_add_azure_resource_types.py` —
  alters the `ResourceType` choices.
- `projects/tags/000X_add_azure_devops_tag_type.py` — adds the new
  `TagType` value.

Squashed where appropriate before merge.

## Out of scope and follow-ups

- Microsoft Entra OAuth.
- Azure DevOps Marketplace extension (separate codebase).
- WIQL / saved-query Boards search.
- Generalising `integrations/vcs/` into a real provider abstraction —
  revisit once GitHub, GitLab, and Azure are all in place so the right
  abstraction is concrete.
- Periodic PAT health check.
- Garbage-collecting `FeatureExternalResource` rows for resources deleted
  on the ADO side.
- Playwright E2E coverage against a live ADO test organisation.
