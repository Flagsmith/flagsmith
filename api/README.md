## Flagsmith API

### Local development

The project assumes the following tools installed:
- [Python](https://www.python.org/downloads/). Any version allowed by `requires-python` in `pyproject.toml` is supported.
- [GNU Make](https://www.gnu.org/software/make/).
- Docker or a compatible tool like [Podman](https://podman.io/). We recommend [OrbStack](https://orbstack.dev/) for macOS.

To install dev dependencies, run `make install`.

To run linters, run `make lint`.

To run tests, run `make docker-up test`.

To prepare a dev database, run `make docker-up django-migrate`.

To bring up a dev server, run `make serve`, or `make serve-with-task-processor` to run the Task processor alongside with the server.

### Code guidelines: testing

The required diff test coverage for our backend PRs is 100%. This policy gives us more confidence to ship, helps us to find bugs earlier, and promotes the test-driven development (TDD) approach. We encourage you to add new tests, and modify existing ones, ahead of writing the code.

This codebase includes two kinds of tests:
- Black box API tests in `tests/integration` directory. Ideally, these are intended to only invoke API endpoints, and verify their output.
- Tests for individual modules, classes and functions in `tests/unit` directory.

We avoid class-based tests. To manage test lifecycle and dependencies, we rely on Pytest features such as fixtures, markers, parametrisation, and hooks. Read `conftest.py` for commonly used fixtures.

We recommend naming test functions using the `test_{subject}__{condition}__{expected outcome}` template, e.g. `test_get_version__valid_file_contents__returns_version_number`.

We use the Given When Then structure in all our tests.

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

### Code guidelines: Flagsmith on Flagsmith

To gate and gradually rollout features in the backend, we use the Flagsmith SDK in local evaluation mode: 

```python
from integrations.flagsmith.client import get_client

flagsmith_client = get_client("local", local_eval=True)
flags = flagsmith_client.get_identity_flags(
    organisation.flagsmith_identifier,
    traits=organisation.flagsmith_on_flagsmith_api_traits,
)
ai_enabled = flags.is_feature_enabled("ai")
```

To modify or add flags, edit [integrations/flagsmith/data/environment.json](integrations/flagsmith/data/environment.json), or run `poetry run python manage.py updateflagsmithenvironment`.
