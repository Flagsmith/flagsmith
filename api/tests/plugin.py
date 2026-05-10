"""
Pytest entry-point plugin for the Flagsmith API test infrastructure.

This module is registered as a ``pytest11`` entry point by ``flagsmith-api``
so that any venv with ``flagsmith-api[dev]`` installed automatically picks up
the ``--ci`` option and every fixture defined in :mod:`tests.fixtures`.

We deliberately do NOT import Django (or ``tests.fixtures``, which imports
Django models at module scope) from this module's top level. Entry-point
plugin modules are imported by pytest before pytest-django's
``pytest_load_initial_conftests`` (``tryfirst=True``) sets up Django, so an
eager import would raise ``AppRegistryNotReady``.

Instead, we register the fixtures lazily from :func:`pytest_configure`, which
runs after pytest-django has initialised Django.
"""

import pytest
from django.test.utils import setup_databases
from pytest_django.plugin import blocking_manager_key


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ci",
        action="store_true",
        default=False,
        help="Enable CI mode",
    )


@pytest.hookimpl(trylast=True)  # type: ignore[misc]
def pytest_configure(config: pytest.Config) -> None:
    # Lazy-import fixtures so its Django model imports run after
    # pytest-django has configured Django.
    from tests import fixtures

    config.pluginmanager.register(fixtures, name="flagsmith-api-fixtures")

    if (
        config.option.ci
        and config.option.dist != "no"
        and not hasattr(config, "workerinput")
    ):
        with config.stash[blocking_manager_key].unblock():
            setup_databases(
                verbosity=config.option.verbose,
                interactive=False,
                parallel=config.option.numprocesses,
            )
