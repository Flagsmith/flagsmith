import pytest
from unittest import mock
from django.db import models
from django.db.models.options import Options
from app import routers


@pytest.mark.parametrize(
    ["given_app_label", "expected_db"],
    [
        ("app_analytics", "analytics"),
        ("another_app", None),
    ],
)
def test_analytics_router_db_for_read__given_app_label__returns_expected_db(
    given_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    mock_model = mock.MagicMock(spec=models.Model)
    mock_model._meta = mock.MagicMock(spec=Options)
    mock_model._meta.app_label = given_app_label
    router = routers.AnalyticsRouter()

    # When
    db = router.db_for_read(mock_model)

    # Then
    assert db == expected_db


@pytest.mark.parametrize(
    ["model_app_label", "expected_db"],
    [
        ("app_analytics", "analytics"),
        ("another_app", None),
    ],
)
def test_analytics_router_db_for_write__given_app_label__returns_expected_db(
    model_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    mock_model = mock.MagicMock(spec=models.Model)
    mock_model._meta = mock.MagicMock(spec=Options)
    mock_model._meta.app_label = model_app_label
    router = routers.AnalyticsRouter()

    # When
    db = router.db_for_write(mock_model)

    # Then
    assert db == expected_db


@pytest.mark.parametrize(
    ["model1_app_label", "model2_app_label", "expected"],
    [
        ("app_analytics", "app_analytics", True),
        ("app_analytics", "another_app", None),
    ],
)
def test_analytics_router_allow_relation__given_app_labels__returns_expected(
    model1_app_label: str,
    model2_app_label: str,
    expected: bool | None,
) -> None:
    # Given
    mock_instance1 = mock.MagicMock(spec=models.Model)
    mock_instance1._meta = mock.MagicMock(spec=Options)
    mock_instance1._meta.app_label = model1_app_label
    mock_instance2 = mock.MagicMock(spec=models.Model)
    mock_instance2._meta = mock.MagicMock(spec=Options)
    mock_instance2._meta.app_label = model2_app_label
    router = routers.AnalyticsRouter()

    # When
    result = router.allow_relation(mock_instance1, mock_instance2)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    ["db_name", "app_label", "expected"],
    [
        ("analytics", "app_analytics", True),
        ("another_db", "app_analytics", None),
        ("default", "app_analytics", None),
        ("analytics", "another_app", False),
    ],
)
def test_analytics_router_allow_migrate__given_db_and_app_label__returns_expected(
    db_name: str,
    app_label: str,
    expected: bool | None,
) -> None:
    # Given
    router = routers.AnalyticsRouter()

    # When
    result = router.allow_migrate(db_name, app_label)

    # Then
    assert result is expected
