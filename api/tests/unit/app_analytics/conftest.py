import pytest
from django.conf import settings


@pytest.fixture
def use_analytics_db(request: pytest.FixtureRequest) -> None:
    """
    Skip tests if no analytics database is configured,
    and make sure the django_db fixture uses both default and analytics databases.
    This is useful to avoid running tests that require a specific database setup.
    """
    if "analytics" not in settings.DATABASES:  # pragma: no cover
        pytest.skip("No analytics database configured, skipping")
        return
    request.applymarker(pytest.mark.django_db(databases=["default", "analytics"]))
    request.getfixturevalue("db")


@pytest.fixture(autouse=True)
def use_analytics_db_marked(request: pytest.FixtureRequest) -> None:
    """
    Automatically skip tests that are marked with 'use_analytics_db'.
    This allows for selective skipping of tests based on the database configuration.
    """
    if request.node.get_closest_marker("use_analytics_db"):
        request.getfixturevalue("use_analytics_db")
