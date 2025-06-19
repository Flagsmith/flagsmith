import pytest
from django.conf import settings


@pytest.fixture
def skip_if_no_analytics_db() -> None:
    """
    Skip tests if no analytics database is configured.
    This is useful to avoid running tests that require a specific database setup.
    """
    if "analytics" not in settings.DATABASES:  # pragma: no cover
        pytest.skip("No analytics database configured, skipping")


@pytest.fixture(autouse=True)
def skip_if_no_analytics_db_marked(request: pytest.FixtureRequest) -> None:
    """
    Automatically skip tests that are marked with 'skip_if_no_analytics_db'.
    This allows for selective skipping of tests based on the database configuration.
    """
    if request.node.get_closest_marker("skip_if_no_analytics_db"):
        request.getfixturevalue("skip_if_no_analytics_db")
