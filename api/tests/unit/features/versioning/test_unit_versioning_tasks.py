import json
from datetime import timedelta
from unittest import mock

import freezegun
import pytest
import responses
from core.constants import STRING
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.exceptions import ValidationError

from environments.identities.models import Identity
from environments.models import Environment, Webhook
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.exceptions import FeatureVersioningError
from features.versioning.models import (
    EnvironmentFeatureVersion,
    VersionChangeSet,
)
from features.versioning.tasks import (
    disable_v2_versioning,
    enable_v2_versioning,
    publish_version_change_set,
    trigger_update_version_webhooks,
)
from features.versioning.versioning_service import (
    get_environment_flags_dict,
    get_environment_flags_queryset,
)
from features.workflows.core.models import ChangeRequest
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType


def test_enable_v2_versioning(
    environment: Environment, feature: Feature, multivariate_feature: Feature
) -> None:
    # When
    enable_v2_versioning(environment.id)

    # Then
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=feature
    ).exists()
    assert EnvironmentFeatureVersion.objects.filter(
        environment=environment, feature=multivariate_feature
    ).exists()

    environment.refresh_from_db()
    assert environment.use_v2_feature_versioning is True


def test_disable_v2_versioning(
    environment_v2_versioning: Environment,
    project: Project,
    feature: Feature,
    segment: Segment,
    staff_user: FFAdminUser,
    identity: Identity,
) -> None:
    # Given
    # First, let's create a new version for the given feature which we'll also add a segment override to
    v2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    v2_environment_flag = v2.feature_states.filter(feature=feature).first()
    v2_environment_flag.enabled = True
    v2_environment_flag.save()

    FeatureState.objects.create(
        feature_segment=FeatureSegment.objects.create(
            environment=environment_v2_versioning,
            feature=feature,
            segment=segment,
            environment_feature_version=v2,
        ),
        feature=feature,
        environment=environment_v2_versioning,
        enabled=True,
        environment_feature_version=v2,
    )

    v2.publish(staff_user)

    # Now, let's create a new version which we won't publish (and hence should be ignored after we disabled
    # v2 versioning)
    v3 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    v3_environment_flag = v3.feature_states.filter(feature=feature).first()
    v3_environment_flag.enabled = False
    v3_environment_flag.save()

    # Let's also create an identity override to confirm it is not affected.
    FeatureState.objects.create(
        identity=identity,
        feature=feature,
        enabled=True,
        environment=environment_v2_versioning,
    )

    # Finally, let's create another environment and confirm its
    # feature states are unaffected.
    unaffected_environment = Environment.objects.create(
        name="Unaffected environment", project=project
    )
    FeatureState.objects.create(
        feature=feature,
        environment=unaffected_environment,
        feature_segment=FeatureSegment.objects.create(
            segment=segment,
            feature=feature,
            environment=unaffected_environment,
        ),
    )

    # When
    disable_v2_versioning(environment_v2_versioning.id)
    environment_v2_versioning.refresh_from_db()

    # Then
    latest_feature_states = get_environment_flags_queryset(
        environment=environment_v2_versioning
    )

    assert latest_feature_states.count() == 3
    assert (
        latest_feature_states.filter(
            feature=feature, feature_segment__isnull=True, identity__isnull=True
        )
        .first()
        .enabled
        is True
    )
    assert (
        latest_feature_states.filter(feature=feature, feature_segment__segment=segment)
        .first()
        .enabled
        is True
    )
    assert (
        latest_feature_states.filter(feature=feature, identity=identity).first().enabled
        is True
    )

    assert unaffected_environment.feature_states.count() == 2
    assert unaffected_environment.feature_segments.count() == 1


@responses.activate
def test_trigger_update_version_webhooks(
    environment_v2_versioning: Environment, feature: Feature
) -> None:
    # Given
    version = EnvironmentFeatureVersion.objects.get(
        feature=feature, environment=environment_v2_versioning
    )
    feature_state = version.feature_states.first()

    webhook_url = "https://example.com/webhook/"
    Webhook.objects.create(environment=environment_v2_versioning, url=webhook_url)

    responses.post(url=webhook_url, status=200)

    # When
    trigger_update_version_webhooks(str(version.uuid))

    # Then
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == webhook_url
    assert json.loads(responses.calls[0].request.body) == {
        "data": {
            "uuid": str(version.uuid),
            "feature": {"id": feature.id, "name": feature.name},
            "published_by": None,
            "feature_states": [
                {
                    "enabled": feature_state.enabled,
                    "value": feature_state.get_feature_state_value(),
                }
            ],
        },
        "event_type": WebhookEventType.NEW_VERSION_PUBLISHED.name,
    }


def test_enable_v2_versioning_for_scheduled_changes(
    environment: Environment, staff_user: FFAdminUser, feature: Feature
) -> None:
    # Given
    now = timezone.now()
    one_from_from_now = now + timedelta(hours=1)
    two_hours_from_now = now + timedelta(hours=2)

    # The current environment feature state for the provided feature
    current_environment_feature_state = FeatureState.objects.get(
        environment=environment, feature=feature
    )

    # A feature state scheduled to go live in the future that is published
    scheduled_change_request = ChangeRequest.objects.create(
        environment=environment, title="Scheduled Change", user=staff_user
    )
    scheduled_feature_state = FeatureState.objects.create(
        feature=feature,
        enabled=True,
        environment=environment,
        live_from=one_from_from_now,
        change_request=scheduled_change_request,
        version=None,
    )
    scheduled_change_request.commit(staff_user)

    # and a feature state scheduled to go live in the future that is not published (and hence
    # shouldn't affect anything)
    unpublished_scheduled_change_request = ChangeRequest.objects.create(
        environment=environment, title="Unpublished Scheduled Change", user=staff_user
    )
    FeatureState.objects.create(
        feature=feature,
        enabled=True,
        environment=environment,
        live_from=two_hours_from_now,
        change_request=unpublished_scheduled_change_request,
        version=None,
    )

    # When
    enable_v2_versioning(environment.id)

    # Then
    environment_flags_queryset_now = get_environment_flags_queryset(environment)
    assert environment_flags_queryset_now.count() == 1
    assert environment_flags_queryset_now.first() == current_environment_feature_state

    with freezegun.freeze_time(one_from_from_now):
        environment_flags_queryset_one_hour_later = get_environment_flags_queryset(
            environment
        )
        assert environment_flags_queryset_one_hour_later.count() == 1
        assert (
            environment_flags_queryset_one_hour_later.first() == scheduled_feature_state
        )

    with freezegun.freeze_time(two_hours_from_now):
        environment_flags_queryset_two_hours_later = get_environment_flags_queryset(
            environment
        )
        assert environment_flags_queryset_two_hours_later.count() == 1
        assert (
            environment_flags_queryset_two_hours_later.first()
            == scheduled_feature_state
        )


def test_publish_version_change_set_sends_email_to_change_request_owner_if_conflicts_when_scheduled(
    feature: Feature,
    environment_v2_versioning: Environment,
    staff_user: FFAdminUser,
    mailoutbox: list[EmailMessage],
) -> None:
    # Given
    live_from = timezone.now() + timedelta(hours=1)

    # First, we need to create the change request, and change set
    # that we want to publish in this test (but should fail because
    # of a conflict with another change set that we will create
    # afterwards and publish immediately).
    change_request_1 = ChangeRequest.objects.create(
        title="CR 1",
        environment=environment_v2_versioning,
        user=staff_user,
    )
    change_set_to_publish = VersionChangeSet.objects.create(
        feature=feature,
        change_request=change_request_1,
        live_from=live_from,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature": feature.id,
                    "enabled": True,
                    "feature_segment": None,
                    "feature_state_value": {"type": "unicode", "string_value": "foo"},
                }
            ]
        ),
    )
    with mock.patch(
        "features.versioning.tasks.publish_version_change_set"
    ) as mock_publish:
        change_request_1.commit(staff_user)
        task_kwargs = {
            "version_change_set_id": change_set_to_publish.id,
            "user_id": staff_user.id,
            "is_scheduled": True,
        }
        mock_publish.delay.assert_called_once_with(
            kwargs=task_kwargs,
            delay_until=live_from,
        )

    # Now, we'll create another change request and change set that will
    # conflict with the first one and publish it immediately.
    conflict_change_request = ChangeRequest.objects.create(
        title="Conflict CR",
        environment=environment_v2_versioning,
        user=staff_user,
    )
    conflict_feature_value = "bar"
    conflict_feature_enabled = False
    VersionChangeSet.objects.create(
        feature=feature,
        change_request=conflict_change_request,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature": feature.id,
                    "enabled": conflict_feature_enabled,
                    "feature_segment": None,
                    "feature_state_value": {
                        "type": "unicode",
                        "string_value": conflict_feature_value,
                    },
                }
            ]
        ),
    )
    conflict_change_request.commit(staff_user)

    # When
    # We simulate the task being called by the task processor at the correct time,
    # as per the mock call that we asserted above.
    with freezegun.freeze_time(live_from):
        publish_version_change_set(**task_kwargs)

    # Then
    # an alert was sent to the change request owner
    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == change_request_1.email_subject
    assert mailoutbox[0].to == [staff_user.email]
    assert mailoutbox[0].body == render_to_string(
        "versioning/scheduled_change_failed_conflict_email.txt",
        context={
            "change_request": change_request_1,
            "user": staff_user,
            "feature": feature,
        },
    )

    # and the change is not reflected in the flags
    latest_flags = get_environment_flags_dict(environment=environment_v2_versioning)
    assert latest_flags[(feature.id, None, None)].enabled is conflict_feature_enabled
    assert (
        latest_flags[(feature.id, None, None)].get_feature_state_value()
        == conflict_feature_value
    )


def test_publish_version_change_set_raises_error_when_segment_override_does_not_exist(
    change_request: ChangeRequest,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    # We create a change set that attempts to update a segment override that
    # doesn't currently exist.
    change_set = VersionChangeSet.objects.create(
        change_request=change_request,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": {"segment": segment.id},
                    "enabled": True,
                    "feature_state_value": {"type": STRING, "string_value": "override"},
                }
            ]
        ),
    )

    # When
    with pytest.raises(ValidationError) as e:
        publish_version_change_set(
            version_change_set_id=change_set.id, user_id=admin_user.id
        )

    # Then
    assert e.value.detail["message"] == (
        f"An unresolvable conflict occurred: segment override does not exist for segment '{segment.name}'."
    )


def test_publish_version_change_set_raises_error_when_serializer_not_valid(
    change_request: ChangeRequest,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
    admin_user: FFAdminUser,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Given
    # We create a change set for which the JSON data is invalid.
    # Note that this should never happen since the data is validated on create.
    change_set = VersionChangeSet.objects.create(
        change_request=change_request, feature=feature, feature_states_to_update="[{}]"
    )

    # When
    with pytest.raises(FeatureVersioningError) as e:
        publish_version_change_set(
            version_change_set_id=change_set.id, user_id=admin_user.id
        )

    # Then
    assert str(e.value) == "Unable to publish version change set"


def test_publish_version_change_set_uses_current_time_for_version_live_from(
    change_request: ChangeRequest,
    feature: Feature,
    environment_v2_versioning: Environment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    now = timezone.now()
    five_minutes_ago = now - timezone.timedelta(minutes=5)

    # a version change_set that sets a live_from a short time in the past
    VersionChangeSet.objects.create(
        change_request=change_request,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": None,
                    "enabled": True,
                    "feature_state_value": {"type": STRING, "string_value": "foo"},
                }
            ]
        ),
        live_from=five_minutes_ago,
    )

    # When
    with freeze_time(now):
        change_request.commit(admin_user)

    # Then
    assert (
        EnvironmentFeatureVersion.objects.get_latest_versions_as_queryset(
            environment_v2_versioning.id
        )
        .get(feature=feature)
        .live_from
        == now
    )
