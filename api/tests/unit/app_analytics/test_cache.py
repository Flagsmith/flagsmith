from app_analytics.cache import CACHE_FLUSH_INTERVAL, APIUsageCache
from app_analytics.models import Resource
from django.utils import timezone
from freezegun import freeze_time
from pytest_mock import MockerFixture


def test_api_usage_cache(mocker: MockerFixture):
    # Given
    cache = APIUsageCache()
    now = timezone.now()
    mocked_track_request_task = mocker.patch("app_analytics.cache.track_request")
    host = "host"
    environment_key_1 = "environment_key_1"
    environment_key_2 = "environment_key_2"

    with freeze_time(now) as frozen_time:
        # Make some tracking requests
        for _ in range(10):
            for resource in Resource:
                cache.track_request(resource, host, environment_key_1)
                cache.track_request(resource, host, environment_key_2)

        # make sure track_request task was not called
        assert not mocked_track_request_task.called

        # Now, let's move the time forward
        frozen_time.tick(CACHE_FLUSH_INTERVAL + 1)

        # let's track another request(to trigger flush)
        cache.track_request(
            Resource.FLAGS,
            host,
            environment_key_1,
        )

        # Then - track request lambda was called for every resource and environment_key combination
        expected_calls = []
        for resource in Resource:
            expected_calls.append(
                mocker.call(
                    kwargs={
                        "resource": resource,
                        "host": host,
                        "environment_key": environment_key_1,
                        "count": 11 if resource == Resource.FLAGS else 10,
                    }
                )
            )
            expected_calls.append(
                mocker.call(
                    kwargs={
                        "resource": resource,
                        "host": host,
                        "environment_key": environment_key_2,
                        "count": 10,
                    }
                )
            )
        mocked_track_request_task.delay.assert_has_calls(expected_calls)


def test_api_usage_cache__track_request_calls_flush_only_after_cache_flush_interval(
    mocker: MockerFixture,
):
    # Given
    mocked_flush = mocker.patch("app_analytics.cache.APIUsageCache.flush")
    cache = APIUsageCache()
    now = timezone.now()

    with freeze_time(now) as frozen_time:
        # When
        for _ in range(10):
            cache.track_request(Resource.FLAGS, "host", "environment_key")

        # Then - flush was not called
        assert not mocked_flush.called

        # Now, let's move the time forward
        frozen_time.tick(CACHE_FLUSH_INTERVAL + 1)

        # call track_request again
        cache.track_request(
            Resource.FLAGS,
            "host",
            "environment_key",
        )

        # Then - flush was called
        assert mocked_flush.called
