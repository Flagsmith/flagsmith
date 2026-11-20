from django.core.cache import BaseCache
from django.core.cache.backends.db import DatabaseCache
from django.core.cache.backends.locmem import LocMemCache
from django.db import ProgrammingError
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from core.health import CACHE_HEALTH_CHECK_KEY, CacheTablesHealthCheck


def test_cache_tables_health_check__all_tables_present__reports_healthy(
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    database_cache = mocker.MagicMock(spec=DatabaseCache)
    database_cache.get.return_value = None
    locmem_cache = mocker.MagicMock(spec=LocMemCache)

    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "db_cache": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "test_db_cache",
        },
    }
    mocker.patch(
        "core.health.caches",
        {"default": locmem_cache, "db_cache": database_cache},
    )
    check = CacheTablesHealthCheck()

    # When
    check.check_status()

    # Then
    assert check.errors == []
    database_cache.get.assert_called_once_with(CACHE_HEALTH_CHECK_KEY)


def test_cache_tables_health_check__table_missing__reports_unhealthy_and_logs(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given
    database_cache = mocker.MagicMock(spec=DatabaseCache)
    database_cache.get.side_effect = ProgrammingError(
        'relation "test_db_cache" does not exist'
    )

    settings.CACHES = {
        "db_cache": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "test_db_cache",
        },
    }
    mocker.patch("core.health.caches", {"db_cache": database_cache})
    check = CacheTablesHealthCheck()

    # When
    check.check_status()

    # Then
    assert len(check.errors) == 1
    assert "db_cache" in str(check.errors[0])
    assert log.has(
        "cache_table.unavailable",
        level="error",
        cache__alias="db_cache",
    )


def test_cache_tables_health_check__non_database_caches__are_skipped(
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    locmem_cache = mocker.MagicMock(spec=LocMemCache)
    redis_cache = mocker.MagicMock(spec=BaseCache)

    settings.CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "redis": {"BACKEND": "django_redis.cache.RedisCache"},
    }
    mocker.patch(
        "core.health.caches",
        {"default": locmem_cache, "redis": redis_cache},
    )
    check = CacheTablesHealthCheck()

    # When
    check.check_status()

    # Then
    assert check.errors == []
    locmem_cache.get.assert_not_called()
    redis_cache.get.assert_not_called()
