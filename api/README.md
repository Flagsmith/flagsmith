## Flagsmith API

### Local development

The project assumes the following tools installed:
- [Python](https://www.python.org/downloads/). Any version allowed by `requires-python` in `pyproject.toml` is supported.
- [GNU Make](https://www.gnu.org/software/make/).
- Docker or a compatible tool like [Podman](https://podman.io/). We recommend [OrbStack](https://orbstack.dev/) for macOS.

To install dev dependencies, run `make install`.

To run linters, run `make lint`.

To run tests, run `make test`.

To run a subset of tests or an individual test, run `make test opts='<pytest args>'`. If the number of test is too low for xdist, consider adding `-n0` to pytest args.

To prepare a dev database, run `make docker-up django-migrate`.

To bring up a dev server, run `make serve`, or `make serve-with-task-processor` to run the Task processor alongside the server.

### Code guidelines: testing

The required diff test coverage for our backend PRs is 100%. This policy gives us more confidence to ship, helps us to find bugs earlier, and promotes the test-driven development (TDD) approach. We encourage you to add new tests, and modify existing ones, ahead of writing the code.

This codebase includes two kinds of tests:
- Black box API tests in `tests/integration` directory. Ideally, these are intended to only invoke API endpoints, and verify their output.
- Tests for individual modules, classes and functions in `tests/unit` directory.

We avoid class-based tests. To manage test lifecycle and dependencies, we rely on Pytest features such as fixtures, markers, parametrisation, and hooks. Read `conftest.py` for commonly used fixtures.

We enforce the `test_{subject}__{condition}__{expected outcome}` template for test names, e.g. `test_get_version__valid_file_contents__returns_version_number`.

We use the Given When Then structure in all our tests.

### Code guidelines: metrics

Flagsmith's backend exports Prometheus metrics. When planning a feature, consider which metrics should cover it — counters for domain events, histograms for latency or sizes, gauges for cardinalities. See [documentation for existing metrics](../docs/docs/deployment-self-hosting/observability/metrics.md). Metrics code is hosted in `metrics.py` modules.

Name metrics `flagsmith_{domain}_{entity}_{unit}` and give them a comprehensive description.

### Code guidelines: logs

We use structured logging to mark up interesting operational and product events. Events emitted via structlog also flow through an OpenTelemetry pipeline and may be routed to a CDP or a data warehouse for product analytics.

When planning a feature, decide which moments deserve an event: things a product manager would ask about (an integration set up, a workflow committed, an import completed), or that a future oncall engineer would need to debug an incident. One well-shaped event per moment beats a wall of free-form `logging.info` calls.

```python
import structlog

# Use logger name as the event domain:
logger = structlog.get_logger("workflows")

# This will produce a `workflows.change_request.committed` OTLP log event
# with the following attributes:
#   - organisation.id
#   - environment.id
#   - feature_states.count
logger.info(
    "change_request.committed",
    organisation__id=environment.project.organisation_id,
    environment__id=environment.id,
    feature_states__count=change_request.feature_states.count(),
)
```

In your tests, verify your logs with the `caplog` fixture:

```python
from pytest_structlog import StructuredLogCapture

def test_my_view__success__logs_expected(
    log: StructuredLogCapture,
) -> None:
    # Given / When
    ...

    # Then
    assert log.events == [
        {
            "level": "info",
            "event": "action.succeeded",
            "organisation__id": organisation.id,
        }
    ]
```

Conventions:

- Logger name is the domain namespace — typically the app or package (`workflows`, `code_references`, `feature_health`).
- Event name is `entity.action` in snake_case (`scan.created`, `change_request.committed`). Do not repeat the logger name in the event, i.e `get_logger("saml")` with `"saml.configuration.created"` is redundant.
- Use double underscore to namespace event attributes, i.e. `namespace__property` will be emitted as `namespace.property`. Include the IDs of the entities the event is about (`organisation__id`, `project__id`, `environment__id`, `feature__id`) so events can be correlated with each other.
- Bind shared context once with `logger.bind(...)` rather than repeating attributes at every call site.
- Avoid PII — identify users and organisations by ID.

For errors, use `logger.exception(...)` or pass `exc_info=exc`, and keep the event name actionable (`import.failed`, not `error`).

### Code guidelines: feature flags (Flagsmith on Flagsmith)

To gate and gradually roll out features in the backend, we use the [OpenFeature](https://openfeature.dev/) SDK with a Flagsmith provider running in local evaluation mode:

```python
from integrations.flagsmith.client import get_openfeature_client

client = get_openfeature_client()
ai_enabled = client.get_boolean_value(
    "ai",
    default_value=False,
    evaluation_context=organisation.openfeature_evaluation_context,
)
```

Organisations expose an `openfeature_evaluation_context` property carrying common traits — use it for org-scoped targeting. For other subjects, build an `EvaluationContext` with a stable `targeting_key` and the attributes your targeting rules need.

Add your feature as early as possible to the Flagsmith on Flagsmith project, and run the `updateflagsmithenvironment` management command to synchronise the local cache. You can use [Flagsmith MCP](https://docs.flagsmith.com/integrating-with-flagsmith/mcp-server) to integrate Flagsmith in your development flow.

### Code guidelines: migrations

To auto-generate migrations for your new code, run `make docker-up django-make-migrations`.

The prompt will ask you for a name and not generate one; we avoid auto-generated migration names.

Squash newly added migrations whenever you can.

### Code guidelines: typing

This codebase, including tests, is fully type-checked by Mypy in strict mode. Resolving existing `# type: ignore` comments is always welcome. If you happen to bring a new `# type: ignore` comment, please document the reason, and consider fixing a small number of adjacent `# type: ignore` comments, if possible and appropriate for the scope of your task.

To run a full type check, run `make typecheck`.

### Code guidelines: design and architecture

Core API consists of Django apps with usual Django submodules like:
- `apps.py`
- `middleware.py`
- `models.py`
- `serializers.py`
- `views.py`
- `urls.py`

We tend to add our own layers in the following modules:
- `constants.py` for app-wide constant variables.
- `dataclasses.py` for dataclass definitions, typically used for internal data transfer objects (DTOs).
- `mappers.py` for data mapping logic unrelated to API requests and responses.
- `services.py` for encapsulated business logic. Our goal with this layer is to make the views, models and serialisers leaner, so that the business logic is more clearly defined and easier to compose.
- `tasks.py` for defining asynchronous and recurring tasks.
- `types.py` for custom type definitions, including typed dicts.
