from django.utils import timezone
from freezegun import freeze_time
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from app_analytics.cache import APIUsageCache, FeatureEvaluationCache
from app_analytics.models import Resource
from app_analytics.types import TrackFeatureEvaluationsByEnvironmentData


def test_api_usage_cache(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.API_USAGE_CACHE_SECONDS = 60

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
                    resource=resource,
                    host=host,
                    environment_key=environment_key_1,
                    labels={},
                )
                cache.track_request(
                    resource=resource,
                    host=host,
                    environment_key=environment_key_2,
                    labels={},
                )

        # make sure track_request task was not called
        assert not mocked_track_request_task.called

        # Now, let's move the time forward
        frozen_time.tick(settings.API_USAGE_CACHE_SECONDS + 1)  # type: ignore[arg-type]

        # let's track another request(to trigger flush)
        cache.track_request(
            resource=Resource.FLAGS,
            host=host,
            environment_key=environment_key_1,
            labels={},
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
                        "labels": {},
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
                        "labels": {},
                    }
                )
            )
        mocked_track_request_task.run_in_thread.assert_has_calls(expected_calls)

        # Next, let's reset the mock
        mocked_track_request_task.reset_mock()

        # and track another request
        cache.track_request(
            resource=Resource.FLAGS,
            host=host,
            environment_key=environment_key_1,
            labels={},
        )

        # finally, make sure track_request task was not called
        assert not mocked_track_request_task.called


def test_feature_evaluation_cache(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FEATURE_EVALUATION_CACHE_SECONDS = 60

    mocked_track_evaluation_task = mocker.patch(
        "app_analytics.cache.track_feature_evaluations_by_environment"
    )
    environment_1_id = 1
    environment_2_id = 2
    feature_1_name = "feature_1_name"
    feature_2_name = "feature_2_name"

    cache = FeatureEvaluationCache()
    now = timezone.now()

    with freeze_time(now) as frozen_time:
        # Track some feature evaluations
        for _ in range(10):
            cache.track_feature_evaluation(
                environment_id=environment_1_id,
                feature_name=feature_1_name,
                evaluation_count=1,
                labels={},
            )
            cache.track_feature_evaluation(
                environment_id=environment_1_id,
                feature_name=feature_2_name,
                evaluation_count=1,
                labels={},
            )
            cache.track_feature_evaluation(
                environment_id=environment_2_id,
                feature_name=feature_2_name,
                evaluation_count=1,
                labels={},
            )

        # Now, let's move the time forward
        frozen_time.tick(settings.FEATURE_EVALUATION_CACHE_SECONDS + 1)  # type: ignore[arg-type]

        # track another evaluation(to trigger cache flush)
        cache.track_feature_evaluation(
            environment_id=environment_1_id,
            feature_name=feature_1_name,
            evaluation_count=1,
            labels={},
        )

        cache.track_feature_evaluation(
            environment_id=environment_1_id,
            feature_name=feature_1_name,
            evaluation_count=1,
            labels={"client_application_name": "test-app"},
        )

        # move time forward again
        frozen_time.tick(settings.FEATURE_EVALUATION_CACHE_SECONDS + 1)  # type: ignore[arg-type]

        # track another one(to trigger cache flush)
        cache.track_feature_evaluation(
            environment_id=environment_1_id,
            feature_name=feature_1_name,
            evaluation_count=1,
            labels={},
        )

        # Assert that the call was made with only the data tracked after the flush interval.
        assert mocked_track_evaluation_task.delay.call_args_list == [
            mocker.call(
                kwargs={
                    "environment_id": 1,
                    "feature_evaluations": [
                        TrackFeatureEvaluationsByEnvironmentData(
                            feature_name="feature_1_name",
                            labels={},
                            evaluation_count=11,
                        ),
                        TrackFeatureEvaluationsByEnvironmentData(
                            feature_name="feature_2_name",
                            labels={},
                            evaluation_count=10,
                        ),
                    ],
                }
            ),
            mocker.call(
                kwargs={
                    "environment_id": 2,
                    "feature_evaluations": [
                        TrackFeatureEvaluationsByEnvironmentData(
                            feature_name="feature_2_name",
                            labels={},
                            evaluation_count=10,
                        )
                    ],
                }
            ),
            mocker.call(
                kwargs={
                    "environment_id": 1,
                    "feature_evaluations": [
                        TrackFeatureEvaluationsByEnvironmentData(
                            feature_name="feature_1_name",
                            labels={"client_application_name": "test-app"},
                            evaluation_count=1,
                        ),
                        TrackFeatureEvaluationsByEnvironmentData(
                            feature_name="feature_1_name",
                            labels={},
                            evaluation_count=1,
                        ),
                    ],
                }
            ),
        ]
