from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture
from task_processor.decorators import TaskHandler

from audit.constants import (
    FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE,
    FEATURE_STATE_WENT_LIVE_MESSAGE,
)
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.tasks import (
    create_audit_log_from_historical_record,
    create_feature_state_updated_by_change_request_audit_log,
    create_feature_state_went_live_audit_log,
    create_segment_priorities_changed_audit_log,
)
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.tasks import enable_v2_versioning
from features.workflows.core.models import ChangeRequest
from segments.models import Segment
from users.models import FFAdminUser


def test_create_audit_log_from_historical_record_does_nothing_if_no_user_or_api_key(  # type: ignore[no-untyped-def]
    mocker,
    monkeypatch,
):
    # Given
    instance = mocker.MagicMock()
    instance.get_audit_log_author.return_value = None
    history_instance = mocker.MagicMock(
        history_id=1, instance=instance, master_api_key=None
    )

    mocked_historical_record_model_class = mocker.MagicMock(
        name="DummyHistoricalRecordModelClass"
    )
    mocked_historical_record_model_class.objects.get.return_value = history_instance

    mocked_user_model_class = mocker.MagicMock()
    mocker.patch("audit.tasks.get_user_model", return_value=mocked_user_model_class)
    mocked_user_model_class.objects.filter.return_value.first.return_value = None

    mocked_audit_log_model_class = mocker.patch("audit.tasks.AuditLog")
    mocked_audit_log_model_class.get_history_record_model_class.return_value = (
        mocked_historical_record_model_class
    )

    history_record_class_path = (
        f"app.models.{mocked_historical_record_model_class.name}"
    )

    # When
    create_audit_log_from_historical_record(
        history_instance.history_id, 1, history_record_class_path
    )

    # Then
    mocked_audit_log_model_class.objects.create.assert_not_called()


def test_create_audit_log_from_historical_record_does_nothing_if_no_log_message(  # type: ignore[no-untyped-def]
    mocker,
    monkeypatch,
):
    # Given
    mock_environment = mocker.MagicMock()

    instance = mocker.MagicMock()
    instance.get_audit_log_author.return_value = None
    instance.get_create_log_message.return_value = None
    instance.get_environment_and_project.return_value = (mock_environment, None)
    history_instance = mocker.MagicMock(
        history_id=1, instance=instance, master_api_key=None, history_type="+"
    )

    history_user = mocker.MagicMock()
    history_user.id = 1

    mocked_historical_record_model_class = mocker.MagicMock(
        name="DummyHistoricalRecordModelClass"
    )
    mocked_historical_record_model_class.objects.get.return_value = history_instance

    mocked_user_model_class = mocker.MagicMock()
    mocker.patch("audit.tasks.get_user_model", return_value=mocked_user_model_class)
    mocked_user_model_class.objects.filter.return_value.first.return_value = (
        history_user
    )

    mocked_audit_log_model_class = mocker.patch("audit.tasks.AuditLog")
    mocked_audit_log_model_class.get_history_record_model_class.return_value = (
        mocked_historical_record_model_class
    )

    history_record_class_path = (
        f"app.models.{mocked_historical_record_model_class.name}"
    )

    # When
    create_audit_log_from_historical_record(
        history_instance.history_id, history_user.id, history_record_class_path
    )

    # Then
    mocked_audit_log_model_class.objects.create.assert_not_called()


def test_create_audit_log_from_historical_record_does_nothing_if_get_skip_create_audit_log_true(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker,
    monkeypatch,
):
    # Given
    instance = mocker.MagicMock()
    instance.get_skip_create_audit_log.return_value = True
    history_instance = mocker.MagicMock(
        history_id=1, instance=instance, master_api_key=None, history_type="+"
    )

    history_user = mocker.MagicMock()
    history_user.id = 1

    mocked_historical_record_model_class = mocker.MagicMock(
        name="DummyHistoricalRecordModelClass"
    )
    mocked_historical_record_model_class.objects.get.return_value = history_instance

    mocked_user_model_class = mocker.MagicMock()
    mocker.patch("audit.tasks.get_user_model", return_value=mocked_user_model_class)
    mocked_user_model_class.objects.filter.return_value.first.return_value = (
        history_user
    )

    mocked_audit_log_model_class = mocker.patch("audit.tasks.AuditLog")
    mocked_audit_log_model_class.get_history_record_model_class.return_value = (
        mocked_historical_record_model_class
    )

    history_record_class_path = (
        f"app.models.{mocked_historical_record_model_class.name}"
    )

    # When
    create_audit_log_from_historical_record(
        history_instance.history_id, history_user.id, history_record_class_path
    )

    # Then
    mocked_audit_log_model_class.objects.create.assert_not_called()


def test_create_audit_log_from_historical_record_creates_audit_log_with_correct_fields(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker,
    monkeypatch,
):
    # Given
    log_message = "a log message"
    related_object_id = 1
    related_object_type = RelatedObjectType.ENVIRONMENT

    mock_environment = mocker.MagicMock(spec=Environment)

    instance = mocker.MagicMock()
    instance.get_skip_create_audit_log.return_value = False
    instance.get_audit_log_author.return_value = None
    instance.get_create_log_message.return_value = log_message
    instance.get_environment_and_project.return_value = mock_environment, None
    instance.get_audit_log_related_object_id.return_value = related_object_id
    instance.get_audit_log_related_object_type.return_value = related_object_type
    instance.get_extra_audit_log_kwargs.return_value = {}
    history_instance = mocker.MagicMock(
        history_id=1,
        instance=instance,
        master_api_key=None,
        history_type="+",
        history_date=timezone.now(),
    )

    history_user = mocker.MagicMock()
    history_user.id = 1

    mocked_historical_record_model_class = mocker.MagicMock(
        name="DummyHistoricalRecordModelClass"
    )
    mocked_historical_record_model_class.objects.get.return_value = history_instance

    mocked_user_model_class = mocker.MagicMock()
    mocker.patch("audit.tasks.get_user_model", return_value=mocked_user_model_class)
    mocked_user_model_class.objects.filter.return_value.first.return_value = (
        history_user
    )

    mocked_audit_log_model_class = mocker.patch("audit.tasks.AuditLog")
    mocked_audit_log_model_class.get_history_record_model_class.return_value = (
        mocked_historical_record_model_class
    )

    history_record_class_path = (
        f"app.models.{mocked_historical_record_model_class.name}"
    )

    # When
    create_audit_log_from_historical_record(
        history_instance.history_id, history_user.id, history_record_class_path
    )

    # Then
    mocked_audit_log_model_class.objects.create.assert_called_once_with(
        history_record_id=history_instance.history_id,
        history_record_class_path=history_record_class_path,
        environment=mock_environment,
        project=None,
        author=history_user,
        related_object_id=related_object_id,
        related_object_type=related_object_type.name,
        log=log_message,
        master_api_key=None,
        created_date=history_instance.history_date,
    )


def test_create_segment_priorities_changed_audit_log(
    admin_user: FFAdminUser,
    feature_segment: FeatureSegment,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    another_segment = Segment.objects.create(
        project=environment.project, name="Another Segment"
    )
    another_feature_segment = FeatureSegment.objects.create(
        feature=feature, environment=environment, segment=another_segment
    )

    now = timezone.now()

    # When
    create_segment_priorities_changed_audit_log(
        previous_id_priority_pairs=[
            (feature_segment.id, 0),
            (another_feature_segment.id, 1),
        ],
        feature_segment_ids=[feature_segment.id, another_feature_segment.id],
        user_id=admin_user.id,
        changed_at=now.isoformat(),
    )

    # Then
    assert AuditLog.objects.filter(
        environment=environment,
        log=f"Segment overrides re-ordered for feature '{feature.name}'.",
        created_date=now,
    ).exists()


def test_create_segment_priorities_changed_audit_log_does_not_create_audit_log_for_versioned_feature_segments(
    admin_user: FFAdminUser,
    feature_segment: FeatureSegment,
    feature: Feature,
    segment_featurestate: FeatureState,
    environment: Environment,
) -> None:
    # Given
    another_segment = Segment.objects.create(
        project=environment.project, name="Another Segment"
    )
    another_feature_segment = FeatureSegment.objects.create(
        feature=feature,
        environment=environment,
        segment=another_segment,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        feature_segment=another_feature_segment,
    )

    now = timezone.now()

    enable_v2_versioning(environment.id)

    feature_segment.refresh_from_db()
    another_feature_segment.refresh_from_db()
    assert feature_segment.environment_feature_version_id is not None
    assert another_feature_segment.environment_feature_version_id is not None

    # When
    create_segment_priorities_changed_audit_log(
        previous_id_priority_pairs=[
            (feature_segment.id, 0),
            (another_feature_segment.id, 1),
        ],
        feature_segment_ids=[feature_segment.id, another_feature_segment.id],
        user_id=admin_user.id,
        changed_at=now.isoformat(),
    )

    # Then
    assert not AuditLog.objects.filter(
        environment=environment,
        log=f"Segment overrides re-ordered for feature '{feature.name}'.",
        created_date=now,
    ).exists()


def test_create_feature_state_went_live_audit_log(
    change_request_feature_state: FeatureState,
) -> None:
    # Given
    message = FEATURE_STATE_WENT_LIVE_MESSAGE % (
        change_request_feature_state.feature.name,
        change_request_feature_state.change_request.title,  # type: ignore[union-attr]
    )
    feature_state_id = change_request_feature_state.id

    # When
    create_feature_state_went_live_audit_log(feature_state_id)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=feature_state_id,
            is_system_event=True,
            log=message,
            created_date=change_request_feature_state.live_from,
        ).count()
        == 1
    )


def test_create_feature_state_went_live_audit_log__rescheduled_feature_update__waits_for_postponed_time(
    caplog: LogCaptureFixture,
    change_request_feature_state: FeatureState,
    mocker: MockerFixture,
) -> None:
    # Given
    future = timezone.now() + timedelta(minutes=1)
    change_request_feature_state.live_from = future
    change_request_feature_state.save()
    delay_task = mocker.patch.object(TaskHandler, "delay")

    # When
    create_feature_state_went_live_audit_log(change_request_feature_state.id)

    # Then
    delay_task.assert_called_once_with(
        delay_until=future,
        args=(change_request_feature_state.id,),
    )
    assert not AuditLog.objects.filter(
        related_object_id=change_request_feature_state.id,
        log__contains="went live",
    ).exists()
    assert (
        "INFO",
        "FeatureState is not due to go live. Likely the change request was rescheduled to a later date.",
    ) in ((record.levelname, record.message) for record in caplog.records)


@pytest.mark.parametrize(
    "scheduled_to, rescheduled_to, "
    "expected_audit_log_early_count, expected_audit_log_late_count, "
    "expected_log_early, expected_log_late",
    [
        # Rescheduled to later
        (timedelta(days=1), timedelta(days=2), 0, 1, True, False),
        # Rescheduled to earlier
        (timedelta(days=2), timedelta(days=1), 1, 0, False, True),
    ],
)
def test_create_feature_state_went_live_audit_log__rescheduled_feature_update__creates_audit_log_at_rescheduled_time(
    caplog: LogCaptureFixture,
    change_request_feature_state: FeatureState,
    change_request: ChangeRequest,
    expected_audit_log_early_count: int,
    expected_audit_log_late_count: int,
    expected_log_early: bool,
    expected_log_late: bool,
    mocker: MockerFixture,
    rescheduled_to: timedelta,
    scheduled_to: timedelta,
) -> None:
    # Given
    now = timezone.now()
    scheduled_time = now + scheduled_to
    rescheduled_time = now + rescheduled_to
    earlier_schedule = min(scheduled_time, rescheduled_time)
    later_schedule = max(scheduled_time, rescheduled_time)

    # Given - the change request is scheduled to go live at `scheduled_time`
    change_request_feature_state.live_from = scheduled_time
    change_request_feature_state.save()
    change_request.committed_at = timezone.now()
    change_request.save()

    # But the change request was rescheduled to go live at `rescheduled_time`
    change_request_feature_state.live_from = rescheduled_time
    change_request_feature_state.save()
    change_request.committed_at = timezone.now()
    change_request.save()

    with freeze_time(earlier_schedule):
        # When
        create_feature_state_went_live_audit_log(change_request_feature_state.id)

        # Then
        assert (
            AuditLog.objects.filter(
                created_date=change_request_feature_state.live_from,
                related_object_id=change_request_feature_state.id,
                log__contains="went live",
            ).count()
            == expected_audit_log_early_count
        )
        assert expected_log_early == (
            (
                "INFO",
                "FeatureState is not due to go live. Likely the change request was rescheduled to a later date.",
            )
            in ((record.levelname, record.message) for record in caplog.records)
        )

    with freeze_time(later_schedule):
        # When
        create_feature_state_went_live_audit_log(change_request_feature_state.id)

        # Then
        assert (
            AuditLog.objects.filter(
                created_date=later_schedule,
                related_object_id=change_request_feature_state.id,
                log__contains="went live",
            ).count()
            == expected_audit_log_late_count
        )
    # Finally, there should be only one audit log for the change request going live
    assert (
        AuditLog.objects.filter(
            created_date=change_request_feature_state.live_from,
            related_object_id=change_request_feature_state.id,
            log__contains="went live",
        ).count()
        == 1
    )


def test_create_feature_state_went_live_audit_log__rescheduled_feature_update__schedules_call_to_feature_update_time(
    caplog: LogCaptureFixture,
    change_request: ChangeRequest,
    change_request_feature_state: FeatureState,
    mocker: MockerFixture,
) -> None:
    # Given
    now = timezone.now()
    near_future = now + timedelta(days=1)
    far_future = near_future + timedelta(days=1)
    create_audit_log = mocker.patch(
        "features.workflows.core.models.create_feature_state_went_live_audit_log",
    )

    with freeze_time(now):
        # When
        change_request_feature_state.live_from = far_future
        change_request_feature_state.save()
        change_request.committed_at = now
        change_request.save()

        # Then
        create_audit_log.delay.assert_called_once_with(
            args=(change_request_feature_state.id,),
            delay_until=far_future,
        )

    # Reset
    change_request = ChangeRequest.objects.get(pk=change_request.pk)
    create_audit_log.reset_mock()

    with freeze_time(now + timedelta(hours=1)):  # A little later
        # When
        change_request_feature_state.live_from = near_future
        change_request_feature_state.save()
        change_request.committed_at = now
        change_request.save()

        # Then
        create_audit_log.delay.assert_called_once_with(
            args=(change_request_feature_state.id,),
            delay_until=near_future,
        )


def test_create_feature_state_updated_by_change_request_audit_log(
    change_request_feature_state: FeatureState,
) -> None:
    # Given
    message = FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE % (
        change_request_feature_state.feature.name,
        change_request_feature_state.change_request.title,  # type: ignore[union-attr]
    )
    feature_state_id = change_request_feature_state.id

    # When
    create_feature_state_updated_by_change_request_audit_log(feature_state_id)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=feature_state_id,
            is_system_event=True,
            log=message,
            created_date=change_request_feature_state.live_from,
        ).count()
        == 1
    )


def test_create_feature_state_updated_by_change_request_audit_log_does_nothing_if_feature_state_deleted(  # type: ignore[no-untyped-def]  # noqa: E501
    change_request_feature_state,
):
    # Given
    change_request_feature_state.delete()
    feature_state_id = change_request_feature_state.id

    # When
    create_feature_state_went_live_audit_log(feature_state_id)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=feature_state_id, is_system_event=True
        ).count()
        == 0
    )


def test_create_feature_state_wen_live_audit_log_does_nothing_if_feature_state_deleted(  # type: ignore[no-untyped-def]  # noqa: E501
    change_request_feature_state,
):
    # Given
    message = FEATURE_STATE_WENT_LIVE_MESSAGE % (
        change_request_feature_state.feature.name,
        change_request_feature_state.change_request.title,
    )
    change_request_feature_state.delete()
    feature_state_id = change_request_feature_state.id

    # When
    create_feature_state_went_live_audit_log(feature_state_id)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=feature_state_id, is_system_event=True, log=message
        ).count()
        == 0
    )
