# Contributing

We're always looking to improve this project! Open source contribution is encouraged so long as they adhere to these
guidelines.

## Pull Requests

The Flagsmith team will be monitoring for pull requests. When we get one, a member of team will test the work against
our internal uses and sign off on the changes. From here, we'll either merge the pull request or provide feedback
suggesting the next steps.

### A couple things to keep in mind

- If you've changed APIs, update the documentation.
- Keep the code style (indents, wrapping) consistent.
- If your PR involves a lot of commits, squash them using `git rebase -i` as this makes it easier for us to review.
- Keep lines under 80 characters.

## Pre-commit

The application uses pre-commit configuration ( `.pre-commit-config.yaml` ) to run `black`, `flake8` and `isort`
formatting before commits.

To install pre-commit:

```bash
# From the repository root
make install
pre-commit install
```

You can also manually run all the checks across the entire codebase with:

```bash
pre-commit run --all-files
```

## Running Tests

The application uses pytest for writing (appropriate use of fixtures) and running tests. Before running tests please
make sure that `DJANGO_SETTINGS_MODULE` env var is pointing to the right module, e.g. `app.settings.test`.

To run tests:

```bash
DJANGO_SETTINGS_MODULE=app.settings.test pytest
```

## Adding Dependencies

We use [Poetry](https://python-poetry.org/) for dependency management - please follow
[their docs on adding dependencies](https://python-poetry.org/docs/basic-usage/#specifying-dependencies).
