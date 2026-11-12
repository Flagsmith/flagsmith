from collections.abc import Iterator

import pytest
from django.apps import apps
from django.db import models

from app import routers
from environments.models import Environment
from features.models import Feature, FeatureState


@pytest.fixture(autouse=True)
def isolate_apps_registry() -> Iterator[None]:
    # Ad-hoc model subclasses defined in these tests register themselves
    # in `apps.all_models` and would otherwise leak into later tests
    # (e.g. makemigrations would propose phantom migrations for them).
    snapshot = {
        app_label: dict(app_models) for app_label, app_models in apps.all_models.items()
    }
    try:
        yield
    finally:
        # Inner dicts must be restored in place: `AppConfig.models` is set to
        # `apps.all_models[label]` by reference at import time, so swapping the
        # outer entry leaves the app config pointing at the polluted dict.
        for app_label, app_models in apps.all_models.items():
            app_models.clear()
            app_models.update(snapshot.get(app_label, {}))
        apps.clear_cache()


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
def test_analytics_router_db_for_write__given_app_label__returns_expected_db(
    model_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    class AnalyticsModel(models.Model):
        class Meta:
            app_label = model_app_label

    router = routers.AnalyticsRouter()

    # When
    db = router.db_for_write(AnalyticsModel)

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
    class AnalyticsModel1(models.Model):
        class Meta:
            app_label = model1_app_label

    class AnalyticsModel2(models.Model):
        class Meta:
            app_label = model2_app_label

    router = routers.AnalyticsRouter()

    # When
    result = router.allow_relation(AnalyticsModel1(), AnalyticsModel2())

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


@pytest.mark.parametrize(
    ["given_app_label", "expected_db"],
    [
        ("clickhouse", "clickhouse"),
        ("another_app", None),
    ],
)
def test_clickhouse_router_db_for_read__given_app_label__returns_expected_db(
    given_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    class ClickHouseModel(models.Model):
        class Meta:
            app_label = given_app_label

    router = routers.ClickHouseRouter()

    # When
    db = router.db_for_read(ClickHouseModel)

    # Then
    assert db == expected_db


@pytest.mark.parametrize(
    ["model_app_label", "expected_db"],
    [
        ("clickhouse", "clickhouse"),
        ("another_app", None),
    ],
)
def test_clickhouse_router_db_for_write__given_app_label__returns_expected_db(
    model_app_label: str,
    expected_db: str | None,
) -> None:
    # Given
    class ClickHouseModel(models.Model):
        class Meta:
            app_label = model_app_label

    router = routers.ClickHouseRouter()

    # When
    db = router.db_for_write(ClickHouseModel)

    # Then
    assert db == expected_db


@pytest.mark.parametrize(
    ["model1_app_label", "model2_app_label", "expected"],
    [
        ("clickhouse", "clickhouse", False),
        ("clickhouse", "another_app", False),
        ("another_app", "clickhouse", False),
        ("another_app", "yet_another_app", None),
    ],
)
def test_clickhouse_router_allow_relation__given_app_labels__returns_expected(
    model1_app_label: str,
    model2_app_label: str,
    expected: bool | None,
) -> None:
    # Given
    class ClickHouseModel1(models.Model):
        class Meta:
            app_label = model1_app_label

    class ClickHouseModel2(models.Model):
        class Meta:
            app_label = model2_app_label

    router = routers.ClickHouseRouter()

    # When
    result = router.allow_relation(ClickHouseModel1(), ClickHouseModel2())

    # Then
    assert result is expected


@pytest.mark.parametrize(
    ["db_name", "app_label", "expected"],
    [
        ("clickhouse", "clickhouse", True),
        ("clickhouse", "another_app", False),
        ("default", "clickhouse", False),
        ("default", "another_app", None),
    ],
)
def test_clickhouse_router_allow_migrate__given_db_and_app_label__returns_expected(
    db_name: str,
    app_label: str,
    expected: bool | None,
) -> None:
    # Given
    router = routers.ClickHouseRouter()

    # When
    result = router.allow_migrate(db_name, app_label)

    # Then
    assert result is expected


@pytest.mark.parametrize(
    ["db1", "db2", "expected"],
    [
        ("default", "default", True),
        ("default", "replica_1", True),
        ("replica_1", "default", True),
        ("replica_1", "replica_2", True),
        ("default", "cross_region_replica_1", True),
        ("replica_1", "cross_region_replica_1", True),
        ("default", None, None),
        (None, None, None),
        ("default", "analytics", None),
        ("analytics", "analytics", None),
        ("replica_1", "task_processor", None),
    ],
)
def test_replica_router_allow_relation__given_databases__returns_expected(
    db1: str | None,
    db2: str | None,
    expected: bool | None,
) -> None:
    # Given
    class SomeModel(models.Model):
        class Meta:
            app_label = "some_app"

    obj1, obj2 = SomeModel(), SomeModel()
    obj1._state.db = db1
    obj2._state.db = db2

    router = routers.ReplicaRouter()

    # When
    result = router.allow_relation(obj1, obj2)

    # Then
    assert result is expected


def test_replica_router_allow_relation__replica_instance__allows_primary_assignment(
    environment: Environment,
    feature: Feature,
) -> None:
    """
    Regression test for https://github.com/Flagsmith/flagsmith/issues/8167 —
    the SDK flags endpoint reads feature states from a replica, then primes the
    `environment` foreign key with the primary-loaded environment.
    """
    # Given
    feature_state = FeatureState.objects.get(
        environment=environment, feature=feature, feature_segment=None, identity=None
    )
    # Simulate a feature state loaded via `using_database_replica`
    feature_state._state.db = "replica_1"

    # When
    feature_state.environment = environment

    # Then
    assert feature_state.environment is environment
