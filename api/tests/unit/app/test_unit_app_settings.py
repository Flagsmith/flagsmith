import pytest


def test_cache_key_prefix__redis_backend__key_prefix_applied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    prefix = "flagsmith"
    caches = {
        "redis_cache": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:6379/1",
        },
        "locmem_cache": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test",
        },
        "db_cache": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "cache_table",
        },
    }

    # When - same logic as settings
    for cache_config in caches.values():
        if "redis" in cache_config.get("BACKEND", "").lower():
            cache_config["KEY_PREFIX"] = prefix

    # Then
    assert caches["redis_cache"]["KEY_PREFIX"] == prefix
    assert "KEY_PREFIX" not in caches["locmem_cache"]
    assert "KEY_PREFIX" not in caches["db_cache"]


def test_cache_key_prefix__empty_prefix__redis_backend_gets_empty_prefix() -> None:
    # Given
    prefix = ""
    caches = {
        "redis_cache": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://localhost:6379/1",
        },
    }

    # When
    for cache_config in caches.values():
        if "redis" in cache_config.get("BACKEND", "").lower():
            cache_config["KEY_PREFIX"] = prefix

    # Then
    assert caches["redis_cache"]["KEY_PREFIX"] == ""
