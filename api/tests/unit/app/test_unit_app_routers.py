import pytest
from django.db import models

from app import routers


@pytest.mark.parametrize(
    ["given_app_label", "expected_db"],
    [
        ("app_analytics", "analytics"),
        ("another_app", None),
    ],
)
def test_AnalyticsRouter_db_for_read__returns_analytics_db_for_analytics_models(
    given_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    class AnalyticsModel(models.Model):
        class Meta:
            app_label = given_app_label

    router = routers.AnalyticsRouter()

    # When
    db = router.db_for_read(AnalyticsModel)

    # Then
    assert db == expected_db


@pytest.mark.parametrize(
    ["model_app_label", "expected_db"],
    [
        ("app_analytics", "analytics"),
        ("another_app", None),
    ],
)
def test_AnalyticsRouter_db_for_write__returns_analytics_db_for_analytics_models(
    model_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    class MyModel(models.Model):
        class Meta:
            app_label = model_app_label

    router = routers.AnalyticsRouter()

    # When
    db = router.db_for_write(MyModel)

    # Then
    assert db == expected_db


@pytest.mark.parametrize(
    ["model1_app_label", "model2_app_label", "expected"],
    [
        ("app_analytics", "app_analytics", True),
        ("app_analytics", "another_app", None),
    ],
)
def test_AnalyticsRouter_allow_relation__allows_relations_between_analytics_models(
    model1_app_label: str,
    model2_app_label: str,
    expected: bool | None,
) -> None:
    # Given
    class MyModel1(models.Model):
        class Meta:
            app_label = model1_app_label

    class MyModel2(models.Model):
        class Meta:
            app_label = model2_app_label

    router = routers.AnalyticsRouter()

    # When
    result = router.allow_relation(MyModel1(), MyModel2())

    # Then
    assert result == expected


@pytest.mark.parametrize(
    ["db_name", "app_label", "expected"],
    [
        ("analytics", "app_analytics", True),
        ("another_db", "app_analytics", False),
        ("default", "app_analytics", None),
        ("analytics", "another_app", None),
    ],
)
def test_AnalyticsRouter_allow_migrate__allows_migrations_on_analytics_db(
    db_name: str,
    app_label: str,
    expected: bool | None,
) -> None:
    # Given
    router = routers.AnalyticsRouter()

    # When
    result = router.allow_migrate(db_name, app_label)

    # Then
    assert result == expected
