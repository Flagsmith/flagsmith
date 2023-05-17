from datetime import timedelta
from typing import Generator

import freezegun
import pytest
from django.utils import timezone

from audit.constants import DATETIME_FORMAT
from environments.identities.models import Identity
from environments.models import Environment
from features.audit_helpers import (
    get_environment_feature_state_created_audit_message,
    get_identity_override_created_audit_message,
    get_segment_override_created_audit_message,
)
from features.models import Feature, FeatureSegment, FeatureState
from segments.models import Segment

_frozen_time = freezegun.freeze_time("04/05/2023 12:12:12")


@pytest.fixture(autouse=True)
def frozen_time() -> Generator[None, None, None]:
    with _frozen_time:
        yield


with _frozen_time:
    one_hour_from_now = timezone.now() + timedelta(hours=1)
    one_hour_ago = timezone.now() - timedelta(hours=1)


@pytest.mark.parametrize(
    "live_from, feature_name, environment_name, identifier, expected_message",
    (
        (
            one_hour_from_now,
            "test_feature",
            "test_environment",
            "test_identity",
            f"Identity override scheduled for {one_hour_from_now.strftime(DATETIME_FORMAT)} "
            f"for feature 'test_feature' and identity 'test_identity'",
        ),
        (
            one_hour_ago,
            "test_feature",
            "test_environment",
            "test_identity",
            "Flag state / Remote config value updated for feature 'test_feature' and identity 'test_identity'",
        ),
    ),
)
def test_get_identity_override_created_audit_message(
    project, live_from, feature_name, environment_name, identifier, expected_message
):
    # Given
    feature = Feature.objects.create(project=project, name=feature_name)
    environment = Environment.objects.create(project=project, name=environment_name)
    identity = Identity.objects.create(environment=environment, identifier=identifier)
    feature_state = FeatureState.objects.create(
        feature=feature, environment=environment, identity=identity, live_from=live_from
    )

    # When
    message = get_identity_override_created_audit_message(feature_state)

    # Then
    assert message == expected_message


@pytest.mark.parametrize(
    "live_from, feature_name, environment_name, segment_name, expected_message",
    (
        (
            one_hour_from_now,
            "test_feature",
            "test_environment",
            "test_segment",
            f"Segment override scheduled for {one_hour_from_now.strftime(DATETIME_FORMAT)} "
            f"for feature 'test_feature' and segment 'test_segment'",
        ),
        (
            one_hour_ago,
            "test_feature",
            "test_environment",
            "test_segment",
            "Flag state / Remote config value updated for feature 'test_feature' and segment 'test_segment'",
        ),
    ),
)
def test_get_segment_override_created_audit_message(
    project, live_from, feature_name, environment_name, segment_name, expected_message
):
    # Given
    feature = Feature.objects.create(project=project, name=feature_name)
    environment = Environment.objects.create(project=project, name=environment_name)
    segment = Segment.objects.create(project=project, name=segment_name)
    feature_segment = FeatureSegment.objects.create(
        segment=segment, environment=environment, feature=feature
    )
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        live_from=live_from,
    )

    # When
    message = get_segment_override_created_audit_message(feature_state)

    # Then
    assert message == expected_message


@pytest.mark.parametrize(
    "live_from, feature_name, environment_name, expected_message",
    (
        (
            one_hour_from_now,
            "test_feature",
            "test_environment",
            f"Flag state / Remote Config value update scheduled for "
            f"{one_hour_from_now.strftime(DATETIME_FORMAT)} for feature: test_feature",
        ),
        (
            one_hour_ago,
            "test_feature",
            "test_environment",
            "New Flag / Remote Config created: test_feature",
        ),
    ),
)
def test_get_environment_feature_state_created_audit_message(
    project, live_from, feature_name, environment_name, expected_message
):
    # Given
    feature = Feature.objects.create(project=project, name=feature_name)
    environment = Environment.objects.create(project=project, name=environment_name)
    feature_state = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        identity=None,
        feature_segment=None,
        live_from=live_from,
        version=2,
    )

    # When
    message = get_environment_feature_state_created_audit_message(feature_state)

    # Then
    assert message == expected_message
