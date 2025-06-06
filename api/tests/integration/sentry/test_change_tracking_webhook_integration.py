import json
import re
from datetime import UTC, datetime, timedelta
from typing import Callable
from unittest.mock import Mock

import freezegun
import pytest
from pytest_mock import MockerFixture

from features.models import Feature, FeatureState
from integrations.sentry import change_tracking
from integrations.sentry.models import SentryChangeTrackingConfiguration


@pytest.fixture
def sentry_configuration(environment: int) -> SentryChangeTrackingConfiguration:
    configuration = SentryChangeTrackingConfiguration(
        environment_id=environment,
        webhook_url="https://sentry.example.com/webhook",
        secret="hush hush!",
    )
    configuration.save()
    return configuration


@pytest.fixture
def requests(mocker: MockerFixture) -> Mock:
    return mocker.patch.object(change_tracking, "requests")


def test_sentry_change_tracking__flag_created__sends_update_to_sentry(
    mocker: MockerFixture,
    project: int,
    requests: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    feature_obj = Feature(
        name="yet_another_feature",
        project_id=project,
    )

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        feature_obj.save()

    # Then
    requests.post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
                "data": [
                    {
                        "action": "created",
                        "created_at": "2199-01-01T00:00:00+00:00",
                        "created_by": {"id": "app@flagsmith.com", "type": "email"},
                        "flag": feature_obj.name,
                    },
                ],
                "meta": {"version": 1},
            },
            sort_keys=True,
        ),
    )
    signature = requests.post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)


def test_sentry_change_tracking__flag_state_change__sends_update_to_sentry(
    feature_name: str,
    feature_state: int,
    mocker: MockerFixture,
    requests: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    feature_state_obj = FeatureState.objects.get(pk=feature_state)

    # When
    with freezegun.freeze_time("2199-01-01T00:00:00.500000+00:00"):
        now = datetime.now(UTC)
        feature_state_obj.enabled = False
        feature_state_obj.live_from = now + timedelta(hours=1)
        feature_state_obj.save()

    # Then
    requests.post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
                "data": [
                    {
                        "action": "updated",
                        "created_at": "2199-01-01T01:00:00+00:00",
                        "created_by": {"id": "app@flagsmith.com", "type": "email"},
                        "change_id": str(feature_state),
                        "flag": feature_name,
                    },
                ],
                "meta": {"version": 1},
            },
            sort_keys=True,
        ),
    )
    signature = requests.post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)


@pytest.mark.parametrize(
    "kaboom",
    [
        lambda feature_state: feature_state.delete(),
        lambda feature_state: feature_state.feature.delete(),
    ],
)
def test_sentry_change_tracking__flag_deleted__sends_update_to_sentry(
    feature_name: str,
    feature_state: int,
    kaboom: Callable[[FeatureState], None],
    mocker: MockerFixture,
    requests: Mock,
    sentry_configuration: SentryChangeTrackingConfiguration,
) -> None:
    # Given
    feature_state_obj = FeatureState.objects.get(pk=feature_state)

    # When
    with freezegun.freeze_time("2199-01-01T01:00:00+00:00"):
        kaboom(feature_state_obj)

    # Then
    requests.post.assert_called_once_with(
        url=sentry_configuration.webhook_url,
        headers={
            "Content-Type": "application/json",
            "X-Sentry-Signature": mocker.ANY,
        },
        data=json.dumps(
            {
                "data": [
                    {
                        "action": "deleted",
                        "created_at": "2199-01-01T01:00:00+00:00",
                        "created_by": {"id": "app@flagsmith.com", "type": "email"},
                        "flag": feature_name,
                    },
                ],
                "meta": {"version": 1},
            },
            sort_keys=True,
        ),
    )
    signature = requests.post.call_args[1]["headers"]["X-Sentry-Signature"]
    assert re.match(r"^[0-9a-f]{64}$", signature)
