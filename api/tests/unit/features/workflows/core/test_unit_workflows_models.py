import json
from datetime import timedelta

import freezegun
import pytest
from django.contrib.sites.models import Site
from django.db.models import Q
from django.utils import timezone
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from freezegun.api import FrozenDateTimeFactory
from pytest_mock import MockerFixture

from audit.constants import (
    CHANGE_REQUEST_APPROVED_MESSAGE,
    CHANGE_REQUEST_COMMITTED_MESSAGE,
    CHANGE_REQUEST_CREATED_MESSAGE,
    ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE,
    FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE,
)
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.models import (
    EnvironmentFeatureVersion,
    VersionChangeSet,
)
from features.versioning.tasks import publish_version_change_set
from features.versioning.versioning_service import get_environment_flags_list
from features.workflows.core.exceptions import (
    CannotApproveOwnChangeRequest,
    ChangeRequestDeletionError,
    ChangeRequestNotApprovedError,
)
from features.workflows.core.models import (
    ChangeRequest,
    ChangeRequestApproval,
    ChangeRequestGroupAssignment,
)
from projects.models import Project
from segments.models import Condition, Segment, SegmentRule
from users.models import FFAdminUser

now = timezone.now()


def test_change_request_approve_by_required_approver(
    change_request_no_required_approvals, mocker
):
    # Given
    mocked_send_mail = mocker.patch("features.workflows.core.models.send_mail")

    user = FFAdminUser.objects.create(email="approver@example.com")
    approval = ChangeRequestApproval.objects.create(
        user=user, change_request=change_request_no_required_approvals
    )
    now = timezone.now()
    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.approve(user=user)

    # Then
    assert change_request_no_required_approvals.approvals.count() == 1
    approval.refresh_from_db()
    assert approval.approved_at == now
    assert approval.user == user

    # 2 emails are sent:
    assert mocked_send_mail.call_count == 2
    assignee_email_call_args, author_email_call_args = mocked_send_mail.call_args_list

    #  1 to the assignee that they are required to approve the CR (done when the ChangeRequestApproval
    #  model object is created above)
    assert assignee_email_call_args.kwargs["recipient_list"] == [user.email]
    assert author_email_call_args.kwargs["fail_silently"] is True

    #  1 to the author that it has been approved
    assert author_email_call_args.kwargs["recipient_list"] == [
        change_request_no_required_approvals.user.email
    ]
    assert author_email_call_args.kwargs["fail_silently"] is True


def test_change_request_approve_by_new_approver_when_no_approvals_exist(
    change_request_no_required_approvals, mocker
):
    # Given
    user = FFAdminUser.objects.create(email="approver@example.com")
    now = timezone.now()
    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.approve(user=user)

    # Then
    approval = change_request_no_required_approvals.approvals.first()
    assert approval.approved_at == now
    assert approval.user == user


def test_change_request_approve_by_new_approver_when_approvals_exist(
    change_request_no_required_approvals, mocker
):
    # Given
    user_1 = FFAdminUser.objects.create(email="user_1@example.com")
    user_2 = FFAdminUser.objects.create(email="user_2@example.com")
    approval = ChangeRequestApproval.objects.create(
        user=user_1, change_request=change_request_no_required_approvals
    )
    now = timezone.now()
    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.approve(user=user_2)

    # Then
    assert change_request_no_required_approvals.approvals.count() == 2

    approval.refresh_from_db()
    assert approval.approved_at is None

    assert change_request_no_required_approvals.approvals.filter(
        user=user_2, approved_at__isnull=False
    ).exists()


def test_change_request_is_approved_returns_true_when_minimum_change_request_approvals_is_none(
    change_request_no_required_approvals, mocker, environment
):
    # Given
    change_request_no_required_approvals.environment.minimum_change_request_approvals = (
        None
    )
    change_request_no_required_approvals.save()
    # Then
    assert change_request_no_required_approvals.is_approved() is True


def test_change_request_commit_raises_exception_when_not_approved(
    change_request_1_required_approvals,
):
    # Given
    user_2 = FFAdminUser.objects.create(email="user_2@example.com")

    # When
    with pytest.raises(ChangeRequestNotApprovedError):
        change_request_1_required_approvals.commit(committed_by=user_2)


def test_change_request_commit_not_scheduled(
    change_request_no_required_approvals, mocker
):
    # Given
    user = FFAdminUser.objects.create(email="approver@example.com")

    now = timezone.now()
    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.commit(committed_by=user)

    # Then
    assert change_request_no_required_approvals.committed_at == now
    assert change_request_no_required_approvals.committed_by == user

    assert change_request_no_required_approvals.feature_states.first().version == 2
    assert change_request_no_required_approvals.feature_states.first().live_from == now


def test_creating_a_change_request_creates_audit_log(environment, admin_user):
    # When
    change_request = ChangeRequest.objects.create(
        environment=environment, title="Change Request", user=admin_user
    )
    # Then
    log = CHANGE_REQUEST_CREATED_MESSAGE % change_request.title
    assert (
        AuditLog.objects.filter(
            related_object_id=change_request.id,
            author=admin_user,
            log=log,
        ).count()
        == 1
    )


def test_approving_a_change_request_creates_audit_logs(
    change_request_no_required_approvals, django_user_model, mocker
):
    # Given
    user = django_user_model.objects.create(email="approver@example.com")

    # When
    ChangeRequestApproval.objects.create(
        change_request=change_request_no_required_approvals,
        user=user,
        approved_at=timezone.now(),
    )

    # Then
    log = CHANGE_REQUEST_APPROVED_MESSAGE % change_request_no_required_approvals.title
    assert (
        AuditLog.objects.filter(
            related_object_id=change_request_no_required_approvals.id,
            author=user,
            log=log,
        ).count()
        == 1
    )


def test_change_request_commit_creates_audit_log(
    change_request_no_required_approvals, mocker, django_assert_num_queries
):
    # Given
    user = FFAdminUser.objects.create(email="approver@example.com")

    # When
    change_request_no_required_approvals.commit(committed_by=user)

    # Then
    log = CHANGE_REQUEST_COMMITTED_MESSAGE % change_request_no_required_approvals.title
    assert (
        AuditLog.objects.filter(
            related_object_id=change_request_no_required_approvals.id,
            author=user,
            log=log,
        ).count()
        == 1
    )


def test_change_request_commit_scheduled(
    change_request_no_required_approvals,
    mocker,
):
    # Given
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    change_request_no_required_approvals.feature_states.update(live_from=tomorrow)

    user = FFAdminUser.objects.create(email="approver@example.com")

    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.commit(committed_by=user)

    # Then
    assert change_request_no_required_approvals.committed_at == now
    assert change_request_no_required_approvals.committed_by == user

    assert change_request_no_required_approvals.feature_states.first().version == 2
    assert (
        change_request_no_required_approvals.feature_states.first().live_from
        == tomorrow
    )


def test_change_request_is_approved_false_when_no_approvals(
    change_request_no_required_approvals, environment_with_1_required_cr_approval
):
    assert change_request_no_required_approvals.is_approved() is False


def test_change_request_is_approved_false_when_unapproved_approvals(
    change_request_no_required_approvals,
    environment_with_1_required_cr_approval,
    django_user_model,
    organisation,
):
    # Given
    user = django_user_model.objects.create(email="user@example.com")
    ChangeRequestApproval.objects.create(
        change_request=change_request_no_required_approvals, user=user
    )

    # Then
    assert change_request_no_required_approvals.is_approved() is False


def test_change_request_is_approved_true_when_enough_approved_approvals(
    change_request_no_required_approvals,
    environment_with_1_required_cr_approval,
    django_user_model,
    organisation,
):
    # Given
    user = django_user_model.objects.create(email="user@example.com")
    change_request_no_required_approvals.approve(user)

    # Then
    assert change_request_no_required_approvals.is_approved() is True


def test_user_cannot_approve_their_own_change_requests(
    change_request_no_required_approvals,
):
    with pytest.raises(CannotApproveOwnChangeRequest):
        change_request_no_required_approvals.approve(
            change_request_no_required_approvals.user
        )


def test_user_is_notified_when_assigned_to_a_change_request(
    change_request_no_required_approvals,
    django_user_model,
    mocker,
    settings,
    mock_render_to_string,
    mock_plaintext_content,
    mock_html_content,
):
    # Given
    mock_send_mail = mocker.patch("features.workflows.core.models.send_mail")
    mocker.patch(
        "features.workflows.core.models.render_to_string", mock_render_to_string
    )

    user = django_user_model.objects.create(email="approver@example.com")

    # When
    ChangeRequestApproval.objects.create(
        change_request=change_request_no_required_approvals, user=user
    )

    # Then
    assert mock_send_mail.call_count == 1
    call_kwargs = mock_send_mail.call_args[1]
    assert call_kwargs["subject"] == change_request_no_required_approvals.email_subject
    assert call_kwargs["message"] == mock_plaintext_content
    assert call_kwargs["html_message"] == mock_html_content
    assert call_kwargs["from_email"] == settings.DEFAULT_FROM_EMAIL
    assert call_kwargs["recipient_list"] == [user.email]


def test_user_is_not_notified_after_approving_a_change_request(
    change_request_no_required_approvals, django_user_model, mocker
):
    # Given
    mock_send_mail = mocker.patch("features.workflows.core.models.send_mail")

    user = django_user_model.objects.create(email="approver@example.com")

    # When
    ChangeRequestApproval.objects.create(
        change_request=change_request_no_required_approvals,
        user=user,
        approved_at=timezone.now(),
    )

    # Then
    # An email is sent to the author but not to the user that approved the request
    assert mock_send_mail.call_count == 1
    assert mock_send_mail.call_args[1]["recipient_list"] == [
        change_request_no_required_approvals.user.email
    ]


def test_change_request_author_is_notified_after_an_approval_is_created(
    mocker,
    change_request_no_required_approvals,
    django_user_model,
    settings,
    mock_render_to_string,
    mock_html_content,
    mock_plaintext_content,
):
    # Given
    mock_send_mail = mocker.patch("features.workflows.core.models.send_mail")
    mocker.patch(
        "features.workflows.core.models.render_to_string", mock_render_to_string
    )

    user = django_user_model.objects.create(email="approver@example.com")

    # When
    ChangeRequestApproval.objects.create(
        change_request=change_request_no_required_approvals,
        user=user,
        approved_at=timezone.now(),
    )

    # Then
    assert mock_send_mail.call_count == 1
    call_kwargs = mock_send_mail.call_args[1]
    assert call_kwargs["subject"] == change_request_no_required_approvals.email_subject
    assert call_kwargs["message"] == mock_plaintext_content
    assert call_kwargs["html_message"] == mock_html_content
    assert call_kwargs["from_email"] == settings.DEFAULT_FROM_EMAIL
    assert call_kwargs["recipient_list"] == [
        change_request_no_required_approvals.user.email
    ]


def test_change_request_author_is_notified_after_an_existing_approval_is_approved(
    mocker,
    django_user_model,
    change_request_no_required_approvals,
    settings,
    mock_render_to_string,
    mock_html_content,
    mock_plaintext_content,
):
    # Given
    mock_send_mail = mocker.patch("features.workflows.core.models.send_mail")
    mocker.patch(
        "features.workflows.core.models.render_to_string", mock_render_to_string
    )

    user = django_user_model.objects.create(email="approver@example.com")

    change_request_approval = ChangeRequestApproval.objects.create(
        change_request=change_request_no_required_approvals, user=user
    )

    # When
    change_request_approval.approved_at = timezone.now()
    change_request_approval.save()

    # Then
    # 2 emails are sent
    assert mock_send_mail.call_count == 2
    call_args_list = mock_send_mail.call_args_list

    # The first one should be to the user that was assigned to approve it
    assert call_args_list[0][1]["recipient_list"] == [user.email]

    # The second one should be to the change request author
    call_kwargs = call_args_list[1][1]
    assert call_kwargs["subject"] == change_request_no_required_approvals.email_subject
    assert call_kwargs["message"] == mock_plaintext_content
    assert call_kwargs["html_message"] == mock_html_content
    assert call_kwargs["from_email"] == settings.DEFAULT_FROM_EMAIL
    assert call_kwargs["recipient_list"] == [
        change_request_no_required_approvals.user.email
    ]


def test_change_request_url(change_request_no_required_approvals, settings):
    # Given
    site = Site.objects.filter(id=settings.SITE_ID).first()
    environment_key = change_request_no_required_approvals.environment.api_key
    project_id = change_request_no_required_approvals.environment.project.id

    # Then
    assert (
        change_request_no_required_approvals.url
        == "https://%s/project/%s/environment/%s/change-requests/%s"
        % (
            site.domain,
            project_id,
            environment_key,
            change_request_no_required_approvals.id,
        )
    )


def test_change_request_email_subject(change_request_no_required_approvals):
    assert (
        change_request_no_required_approvals.email_subject
        == "Flagsmith Change Request: %s (#%s)"
        % (
            change_request_no_required_approvals.title,
            change_request_no_required_approvals.id,
        )
    )


def test_committing_cr_after_live_from_creates_correct_audit_log_for_related_feature_states(
    settings, change_request_no_required_approvals, mocker, admin_user
):
    # Given
    mock_create_feature_state_went_live_audit_log = mocker.patch(
        "features.workflows.core.models.create_feature_state_went_live_audit_log"
    )

    assert change_request_no_required_approvals.feature_states.exists()

    # When
    change_request_no_required_approvals.commit(committed_by=admin_user)

    # Then
    mock_create_feature_state_went_live_audit_log.delay.assert_not_called()
    for feature_state in change_request_no_required_approvals.feature_states.all():
        log = FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE % (
            feature_state.feature.name,
            feature_state.change_request.title,
        )
        assert (
            AuditLog.objects.filter(
                related_object_id=feature_state.id,
                related_object_type=RelatedObjectType.FEATURE_STATE.name,
                log=log,
            ).count()
            == 1
        )


def test_committing_cr_after_before_from_schedules_tasks_correctly(
    settings, change_request_no_required_approvals, mocker, admin_user
):
    # Given
    mock_create_feature_state_went_live_audit_log = mocker.patch(
        "features.workflows.core.models.create_feature_state_went_live_audit_log"
    )

    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    change_request_no_required_approvals.feature_states.all().update(live_from=tomorrow)

    # When
    change_request_no_required_approvals.commit(committed_by=admin_user)

    # Then
    mock_create_feature_state_went_live_audit_log.delay.assert_called_once_with(
        delay_until=tomorrow,
        args=(change_request_no_required_approvals.feature_states.all().first().id,),
    )


@pytest.mark.freeze_time()
def test_committing_scheduled_change_requests_results_in_correct_versions(
    environment, feature, admin_user, freezer
):
    # Given
    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)
    two_hours_from_now = now + timedelta(hours=2)
    three_hours_from_now = now + timedelta(hours=3)

    scheduled_cr_1 = ChangeRequest.objects.create(
        title="scheduled_cr_1", environment=environment, user=admin_user
    )
    FeatureState.objects.create(
        environment=environment,
        feature=feature,
        live_from=one_hour_from_now,
        version=None,
        change_request=scheduled_cr_1,
    )

    scheduled_cr_2 = ChangeRequest.objects.create(
        title="scheduled_cr_2", environment=environment, user=admin_user
    )
    cr_2_fs = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        live_from=two_hours_from_now,
        version=None,
        change_request=scheduled_cr_2,
    )

    # When
    # we commit the change requests in the 'wrong' order
    scheduled_cr_2.commit(admin_user)
    scheduled_cr_1.commit(admin_user)

    # and move time on to after the feature states from both CRs should have gone live
    freezer.move_to(three_hours_from_now)

    # Then
    # the feature state in the latest scheduled cr should be the one that is returned
    feature_states = get_environment_flags_list(environment=environment)
    assert len(feature_states) == 1
    assert feature_states[0] == cr_2_fs


def test_change_request_group_assignment_sends_notification_emails_to_group_users(
    change_request, user_permission_group, settings, mocker
):
    # Given
    change_request_group_assignment = ChangeRequestGroupAssignment(
        change_request=change_request, group=user_permission_group
    )

    workflows_logic_tasks_module_mock = mocker.MagicMock()

    mocked_importlib = mocker.patch("features.workflows.core.models.importlib")
    mocked_importlib.import_module.return_value = workflows_logic_tasks_module_mock

    settings.WORKFLOWS_LOGIC_INSTALLED = True

    # When
    change_request_group_assignment.save()

    # Then
    workflows_logic_tasks_module_mock.notify_group_of_change_request_assignment.delay.assert_called_once_with(
        kwargs={
            "change_request_group_assignment_id": change_request_group_assignment.id
        }
    )


@pytest.mark.freeze_time(now)
def test_commit_change_request_publishes_environment_feature_versions(
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    mocker: MockerFixture,
):
    # Given
    environment.use_v2_feature_versioning = True
    environment.save()

    feature_state = environment.feature_states.first()

    change_request = ChangeRequest.objects.create(
        title="Test CR", environment=environment, user=admin_user
    )

    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )
    environment_feature_version.feature_states.add(
        feature_state.clone(env=environment, as_draft=True)
    )

    change_request.environment_feature_versions.add(environment_feature_version)

    mock_rebuild_environment_document_task = mocker.patch(
        "features.workflows.core.models.rebuild_environment_document"
    )
    mock_trigger_update_version_webhooks = mocker.patch(
        "features.workflows.core.models.trigger_update_version_webhooks"
    )

    # When
    change_request.commit(admin_user)

    # Then
    environment_feature_version.refresh_from_db()
    assert environment_feature_version.published
    assert environment_feature_version.published_by == admin_user
    assert environment_feature_version.live_from == now

    mock_rebuild_environment_document_task.delay.assert_called_once_with(
        kwargs={"environment_id": environment.id},
        delay_until=environment_feature_version.live_from,
    )
    mock_trigger_update_version_webhooks.delay.assert_called_once_with(
        kwargs={
            "environment_feature_version_uuid": str(environment_feature_version.uuid)
        },
        delay_until=environment_feature_version.live_from,
    )


def test_cannot_delete_committed_change_request(
    change_request: ChangeRequest, admin_user: FFAdminUser
) -> None:
    # Given
    change_request.commit(admin_user)
    change_request.save()

    # When
    with pytest.raises(ChangeRequestDeletionError):
        change_request.delete()

    # Then
    # exception raised


def test_can_delete_committed_change_request_scheduled_for_the_future(
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        change_request=change_request,
        live_from=timezone.now() + timedelta(days=1),
        version=None,
    )

    change_request.commit(admin_user)
    change_request.save()

    # When
    change_request.delete()

    # Then
    assert not ChangeRequest.objects.filter(id=change_request.id).exists()


def test_can_delete_committed_change_request_scheduled_for_the_future_with_environment_feature_versions(
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        feature=feature,
        environment=environment,
        live_from=timezone.now() + timedelta(days=1),
        change_request=change_request,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        environment_feature_version=environment_feature_version,
        version=None,
    )

    change_request.commit(admin_user)
    change_request.save()

    # When
    change_request.delete()

    # Then
    assert not ChangeRequest.objects.filter(id=change_request.id).exists()


def test_committing_change_request_with_environment_feature_versions_creates_publish_audit_log(
    feature: Feature, environment_v2_versioning: Environment, admin_user: FFAdminUser
) -> None:
    # Given
    change_request = ChangeRequest.objects.create(
        title="Test CR",
        environment=environment_v2_versioning,
        user=admin_user,
    )

    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning,
        feature=feature,
        change_request=change_request,
    )

    # When
    change_request.commit(admin_user)

    # Then
    assert AuditLog.objects.filter(
        related_object_uuid=environment_feature_version.uuid,
        related_object_type=RelatedObjectType.EF_VERSION.name,
        log=ENVIRONMENT_FEATURE_VERSION_PUBLISHED_MESSAGE % feature.name,
    ).exists()


def test_change_request_live_from_for_change_request_with_change_set(
    feature: Feature,
    environment_v2_versioning: Environment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    change_request = ChangeRequest.objects.create(
        title="Test CR",
        environment=environment_v2_versioning,
        user=admin_user,
    )
    VersionChangeSet.objects.create(
        change_request=change_request,
        feature=feature,
        feature_states_to_update=json.dumps(
            [
                {
                    "feature_segment": None,
                    "enabled": True,
                    "feature_state_value": {
                        "type": "unicode",
                        "string_value": "updated",
                    },
                }
            ]
        ),
    )

    # When
    now = timezone.now()
    with freezegun.freeze_time(now):
        change_request.commit(admin_user)

    # Then
    assert change_request.live_from == now


def test_ignore_conflicts_for_multiple_scheduled_change_requests(
    feature: Feature,
    environment_v2_versioning: Environment,
    admin_user: FFAdminUser,
    project: Project,
    freezer: FrozenDateTimeFactory,
    mocker: MockerFixture,
) -> None:
    """
    This test is for the specific use case where we want to schedule a slow
    roll-out for a feature.
    """
    # We are going to simulate the task processor ourselves, so let's mock it so we can assert
    # the required calls later.
    mock_publish_version_change_set = mocker.patch(
        "features.versioning.tasks.publish_version_change_set"
    )

    # First, let's create the 2 percentage split segments that we want to use for the roll-out
    def _create_segment(percentage_value: int) -> Segment:
        segment = Segment.objects.create(
            name=f"percentage_split_segment_{percentage_value}", project=project
        )
        parent_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        child_rule = SegmentRule.objects.create(
            rule=parent_rule, type=SegmentRule.ANY_RULE
        )
        Condition.objects.create(
            rule=child_rule, property=PERCENTAGE_SPLIT, value=str(percentage_value)
        )
        return segment

    ten_percent_segment = _create_segment(10)
    twenty_percent_segment = _create_segment(20)

    now = timezone.now()
    ten_minutes_from_now = now + timedelta(minutes=10)
    twenty_minutes_from_now = now + timedelta(minutes=20)

    # Now, let's create our change requests to create the 2 overrides in the future
    change_requests = []
    for segment_to_add, live_from, segments_to_delete in [
        (ten_percent_segment, ten_minutes_from_now, []),
        (twenty_percent_segment, twenty_minutes_from_now, [ten_percent_segment]),
    ]:
        change_request = ChangeRequest.objects.create(
            title="Scheduled CR1",
            environment=environment_v2_versioning,
            user=admin_user,
        )
        version_change_set = VersionChangeSet.objects.create(
            change_request=change_request,
            feature=feature,
            feature_states_to_create=json.dumps(
                [
                    {
                        "feature_segment": {
                            "segment": segment_to_add.id,
                        },
                        "enabled": True,
                        "feature_state_value": {"type": "unicode", "string_value": ""},
                    }
                ]
            ),
            segment_ids_to_delete_overrides=json.dumps(
                [s.id for s in segments_to_delete]
            ),
            live_from=live_from,
        )
        change_requests.append(change_request)
        change_request.commit(committed_by=admin_user)
        mock_publish_version_change_set.delay.assert_called_once_with(
            kwargs={
                "version_change_set_id": version_change_set.id,
                "user_id": admin_user.id,
                "is_scheduled": True,
            },
            delay_until=live_from,
        )
        mock_publish_version_change_set.reset_mock()

    mock_publish_version_change_set.stop()

    # Now, let's move time forward and publish the first change request (note: this is
    # simulating the task processor picking up the task that we mock asserted earlier)
    freezer.move_to(ten_minutes_from_now)
    publish_version_change_set(
        version_change_set_id=change_requests[0].change_sets.first().id,
        user_id=admin_user.id,
        is_scheduled=True,
    )

    after_cr_1_flags = get_environment_flags_list(
        environment=environment_v2_versioning,
        additional_filters=Q(feature_segment__isnull=False),
    )
    assert len(after_cr_1_flags) == 1
    assert after_cr_1_flags[0].feature_segment.segment == ten_percent_segment

    # Now, let's move time forward again and publish the second change request
    freezer.move_to(twenty_minutes_from_now)
    publish_version_change_set(
        version_change_set_id=change_requests[1].change_sets.first().id,
        user_id=admin_user.id,
        is_scheduled=True,
    )

    after_cr_1_flags = get_environment_flags_list(
        environment=environment_v2_versioning,
        additional_filters=Q(feature_segment__isnull=False),
    )
    assert len(after_cr_1_flags) == 1
    assert after_cr_1_flags[0].feature_segment.segment == twenty_percent_segment
