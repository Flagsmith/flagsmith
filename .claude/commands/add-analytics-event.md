---
description: Add a structlog analytics event to the backend following Flagsmith OTel conventions
---

Add a structlog analytics event to the Flagsmith backend.

## Arguments

- `$ARGUMENTS` = "" → Ask the user what business action to instrument
- `$ARGUMENTS` = "SAML configuration created" → Add an event for that action

---

## Step 1 — Clarify the event

If `$ARGUMENTS` is empty, ask:
- What business action should be instrumented? (e.g. "user invited to organisation", "change request committed")
- Which file / function / view triggers it?

Otherwise, derive intent from `$ARGUMENTS` and proceed.

---

## Step 2 — Choose the event name

The event name is composed of two parts that are **kept separate**:

- **Logger name** (`structlog.get_logger("domain")`) — the domain/app namespace, e.g. `"saml"`, `"code_references"`, `"workflows"`
- **Event string** — the action in dot-notation, e.g. `"configuration.created"`, `"scan.created"`, `"change_request.committed"`

The OTel processor automatically combines them as `"{logger_name}.{event}"` when emitting to OTel, so **do not repeat the domain in the event string**.

| Logger | Event string | OTel event name (auto-generated) |
|---|---|---|
| `get_logger("saml")` | `"configuration.created"` | `saml.configuration.created` |
| `get_logger("code_references")` | `"scan.created"` | `code_references.scan.created` |
| `get_logger("workflows")` | `"change_request.committed"` | `workflows.change_request.committed` |

Use `snake_case` for both the logger name and event string. Use past tense for actions (`created`, `committed`, `deleted`).

---

## Step 3 — Choose the right file

Find the best instrumentation point:

- **ViewSet create/destroy** → override `perform_create` / `perform_destroy`
- **Service layer** → add directly after the core operation succeeds
- **Signal or task** → add at the end of the handler, after side effects

Prefer service-layer instrumentation over view-layer when the action can be triggered from multiple places (API, management commands, tasks).

Read the target file before editing.

---

## Step 4 — Add the logger

If the file doesn't already import structlog, add it at the top with the other imports:

```python
import structlog
```

Then declare a module-level logger named after the domain:

```python
logger = structlog.get_logger("domain")
```

If the file already has a `logging.getLogger(__name__)` logger, keep it — add the structlog logger alongside it with a different name (e.g. `analytics_logger` or rename to avoid shadowing).

---

## Step 5 — Emit the event

Call `logger.info(...)` **after** the operation succeeds (not before, not in a finally block):

```python
logger.info(
    "action.past_tense",   # no domain prefix — the logger name provides it
    organisation__id=instance.organisation_id,
    # add other relevant fields below
)
```

### Field naming conventions

| Pattern | Example | Meaning |
|---|---|---|
| `organisation__id` | `organisation__id=42` | FK reference (maps to `organisation.id` in OTel) |
| `environment__id` | `environment__id=7` | FK reference |
| `feature__id` | `feature__id=99` | FK reference |
| `*__count` | `feature_states__count=3` | Count of related objects |
| Plain name | `plan_id="scale-up-v2"` | Scalar value, no nesting |

Double underscores (`__`) are automatically converted to dots by the OTel processor (`organisation__id` → `organisation.id` attribute in OTel).

Always include `organisation__id` — it is the primary analytics grouping key.

### What NOT to log

- PII: email addresses, names, IP addresses
- Secrets: tokens, API keys, passwords
- High-cardinality noise: raw request bodies, full stack traces (those go to Sentry)

---

## Step 6 — Write a test

Add a test in the corresponding `tests/unit/` path using `pytest_structlog`:

```python
from pytest_structlog import StructuredLogCapture

def test_{subject}__{condition}__emits_structlog_event(
    log: StructuredLogCapture,
    # ... fixtures
) -> None:
    # Given
    # ... set up

    # When
    # ... call the function / endpoint

    # Then
    assert {
        "event": "action.past_tense",  # matches the string passed to logger.info(), not the full OTel name
        "level": "info",
        "organisation__id": organisation.id,
        # other fields you logged
    } in log.events
```

The `log` fixture is provided by `pytest-structlog` — no import needed beyond `StructuredLogCapture` for the type annotation.

### Real examples to reference

- `tests/unit/features/workflows/core/test_unit_workflows_models.py` — `change_request.committed`
- `tests/unit/projects/code_references/test_unit_projects_code_references_views.py` — `scan.created`
- `tests/unit/organisations/subscriptions/test_unit_subscriptions_permissions.py` — permissions with mocker

---

## Step 7 — Verify

Run only the new test file to confirm it passes:

```bash
make test opts='path/to/test_file.py -n0'
```

Then run mypy on both edited files:

```bash
make typecheck
```

---

## Step 8 — Report

Summarise:
- Event name emitted
- File instrumented and line number
- Fields included
- Test file created/updated
- Suggest a commit message
