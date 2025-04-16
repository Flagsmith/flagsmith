from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from app_analytics.cache import APIUsageCache, FeatureEvaluationCache
from app_analytics.models import Resource


def test_api_usage_cache(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.PG_API_USAGE_CACHE_SECONDS = 60

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
                cache.track_request(
                    resource,
                    host,
                    environment_key_1,
                )
                cache.track_request(
                    resource,
                    host,
                    environment_key_2,
                )

        # make sure track_request task was not called
        assert not mocked_track_request_task.called

        # Now, let's move the time forward
        frozen_time.tick(settings.PG_API_USAGE_CACHE_SECONDS + 1)  # type: ignore[arg-type]

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
                        "resource": resource.value,
                        "host": host,
                        "environment_key": environment_key_1,
                        "count": 11 if resource == Resource.FLAGS else 10,
                    }
                )
            )
            expected_calls.append(
                mocker.call(
                    kwargs={
                        "resource": resource.value,
                        "host": host,
                        "environment_key": environment_key_2,
                        "count": 10,
                    }
                )
            )
        mocked_track_request_task.delay.assert_has_calls(expected_calls)

        # Next, let's reset the mock
        mocked_track_request_task.reset_mock()

        # and track another request
        cache.track_request(
            Resource.FLAGS,
            host,
            environment_key_1,
        )

        # finally, make sure track_request task was not called
        assert not mocked_track_request_task.called


def test_feature_evaluation_cache(  # type: ignore[no-untyped-def]
    mocker: MockerFixture,
    settings: SettingsWrapper,
):
    # Given
    settings.FEATURE_EVALUATION_CACHE_SECONDS = 60
    settings.USE_POSTGRES_FOR_ANALYTICS = False
    settings.INFLUXDB_TOKEN = "token"

    mocked_track_evaluation_task = mocker.patch(
        "app_analytics.cache.track_feature_evaluation"
    )
    mocked_track_feature_evaluation_influxdb_task = mocker.patch(
        "app_analytics.cache.track_feature_evaluation_influxdb"
    )
    environment_1_id = 1
    environment_2_id = 2
    feature_1_name = "feature_1_name"
    feature_2_name = "feature_2_name"

    cache = FeatureEvaluationCache()  # type: ignore[no-untyped-call]
    now = timezone.now()

    with freeze_time(now) as frozen_time:
        # Track some feature evaluations
        for _ in range(10):
            cache.track_feature_evaluation(environment_1_id, feature_1_name, 1)
            cache.track_feature_evaluation(environment_1_id, feature_2_name, 1)
            cache.track_feature_evaluation(environment_2_id, feature_2_name, 1)

        # Make sure the internal tasks were not called
        assert not mocked_track_evaluation_task.delay.called
        assert not mocked_track_feature_evaluation_influxdb_task.delay.called

        # Now, let's move the time forward
        frozen_time.tick(settings.FEATURE_EVALUATION_CACHE_SECONDS + 1)  # type: ignore[arg-type]

        # track another evaluation(to trigger cache flush)
        cache.track_feature_evaluation(environment_1_id, feature_1_name, 1)

        # Then
        mocked_track_feature_evaluation_influxdb_task.delay.assert_has_calls(
            [
                mocker.call(
                    kwargs={
                        "environment_id": environment_1_id,
                        "feature_evaluations": {
                            feature_1_name: 11,
                            feature_2_name: 10,
                        },
                    },
                ),
                mocker.call(
                    kwargs={
                        "environment_id": environment_2_id,
                        "feature_evaluations": {feature_2_name: 10},
                    },
                ),
            ]
        )
        # task responsible for tracking evaluation using postgres was not called
        assert not mocked_track_evaluation_task.delay.called

        # Next, let's enable postgres tracking
        settings.USE_POSTGRES_FOR_ANALYTICS = True

        # rest the mock
        mocked_track_feature_evaluation_influxdb_task.reset_mock()

        # Track another evaluation
        cache.track_feature_evaluation(environment_1_id, feature_1_name, 1)

        # move time forward again
        frozen_time.tick(settings.FEATURE_EVALUATION_CACHE_SECONDS + 1)  # type: ignore[arg-type]

        # track another one(to trigger cache flush)
        cache.track_feature_evaluation(environment_1_id, feature_1_name, 1)

        # Assert that the call was made with only the data tracked after the flush interval.
        mocked_track_evaluation_task.delay.assert_called_once_with(
            kwargs={
                "environment_id": environment_1_id,
                "feature_evaluations": {feature_1_name: 2},
            }
        )
        # and the task for influx was not called
        assert not mocked_track_feature_evaluation_influxdb_task.delay.called
