import pytest
from django.test.utils import setup_databases
from pytest_django.plugin import blocking_manager_key

# Re-export every fixture defined in `tests.fixtures` so pytest discovers them
# when running the api's own test suite. The fixtures live in a regular module
# (rather than in this conftest) so that downstream consumers that install the
# api package can do `from tests.fixtures import *` from their own conftest
# without colliding with this top-level `conftest` py-module.
from tests.fixtures import *  # noqa: F401, F403


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--ci",
        action="store_true",
        default=False,
        help="Enable CI mode",
    )


@pytest.hookimpl(trylast=True)  # type: ignore[misc]
def pytest_configure(config: pytest.Config) -> None:
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
