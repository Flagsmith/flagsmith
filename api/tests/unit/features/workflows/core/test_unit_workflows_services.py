from datetime import timedelta

import pytest
from django.utils import timezone
from flag_engine.segments.constants import EQUAL, PERCENTAGE_SPLIT
from pytest_mock import MockerFixture

from core.workflows_services import ChangeRequestCommitService
from environments.models import Environment
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import get_environment_flags_list
from features.workflows.core.exceptions import ChangeRequestNotApprovedError
from features.workflows.core.models import ChangeRequest
from segments.models import Condition, Segment, SegmentRule
from segments.services import SegmentCloneService
from users.models import FFAdminUser

now = timezone.now()


def test_webhooks_is_triggered_when_commiting_a_change_request(
    mocker: MockerFixture,
    environment: Environment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mock_trigger_feature_state_change_webhooks = mocker.patch(
        "core.workflows_services.trigger_feature_state_change_webhooks"
    )
    feature = Feature.objects.create(
        name="test_feature_for_change_request", project=environment.project
    )
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        enabled=True,
        version=2,
    )
    change_request = ChangeRequest.objects.create(
        environment=environment, title="Test Change Request", user=admin_user
    )
    commit_service = ChangeRequestCommitService(change_request)
    feature_state = FeatureState.objects.create(
        feature=feature,
        change_request=change_request,
        environment=feature_state.environment,
        enabled=False,
        version=None,
    )

    # When
    commit_service.commit(committed_by=admin_user)

    # Then
    assert change_request.is_committed is True
    mock_trigger_feature_state_change_webhooks.assert_called_once()
    call = mock_trigger_feature_state_change_webhooks.call_args
    _, kwargs = call
    assert kwargs["instance"].feature_id == feature_state.feature_id
    assert kwargs["instance"].environment_id == feature_state.environment_id
    assert kwargs["instance"].id == feature_state.id
    assert kwargs["instance"].enabled is False
    assert kwargs["previous_instance"].id != feature_state.id
    assert kwargs["previous_instance"].version == 2
    assert kwargs["previous_instance"].feature_id == feature_state.feature_id
    assert kwargs["previous_instance"].environment_id == feature_state.environment_id
    assert kwargs["previous_instance"].enabled is True


def test_change_request_is_approved_returns_true_when_minimum_change_request_approvals_is_none(  # type: ignore[no-untyped-def]  # noqa: E501
    change_request_no_required_approvals, mocker, environment
):
    # Given
    change_request_no_required_approvals.environment.minimum_change_request_approvals = None
    change_request_no_required_approvals.save()
    # Then
    assert change_request_no_required_approvals.is_approved() is True


def test_change_request_commit_raises_exception_when_not_approved(  # type: ignore[no-untyped-def]
    change_request_1_required_approvals,
):
    # Given
    user_2 = FFAdminUser.objects.create(email="user_2@example.com")

    commit_service = ChangeRequestCommitService(change_request_1_required_approvals)
    # When
    with pytest.raises(ChangeRequestNotApprovedError):
        commit_service.commit(committed_by=user_2)


def test_change_request_commit_not_scheduled(  # type: ignore[no-untyped-def]
    change_request_no_required_approvals, mocker
):
    # Given
    user = FFAdminUser.objects.create(email="approver@example.com")
    commit_service = ChangeRequestCommitService(change_request_no_required_approvals)
    now = timezone.now()
    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    commit_service.commit(committed_by=user)

    # Then
    assert change_request_no_required_approvals.committed_at == now
    assert change_request_no_required_approvals.committed_by == user

    assert change_request_no_required_approvals.feature_states.first().version == 2
    assert change_request_no_required_approvals.feature_states.first().live_from == now


def test_change_request_commit_scheduled(  # type: ignore[no-untyped-def]
    change_request_no_required_approvals,
    mocker,
):
    # Given
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    change_request_no_required_approvals.feature_states.update(live_from=tomorrow)

    user = FFAdminUser.objects.create(email="approver@example.com")
    commit_service = ChangeRequestCommitService(change_request_no_required_approvals)
    mocker.patch("features.workflows.core.models.timezone.now", return_value=now)

    # When
    commit_service.commit(committed_by=user)

    # Then
    assert change_request_no_required_approvals.committed_at == now
    assert change_request_no_required_approvals.committed_by == user

    assert change_request_no_required_approvals.feature_states.first().version == 2
    assert (
        change_request_no_required_approvals.feature_states.first().live_from
        == tomorrow
    )


@pytest.mark.freeze_time()
def test_committing_scheduled_change_requests_results_in_correct_versions(  # type: ignore[no-untyped-def]
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
    commit_service = ChangeRequestCommitService(scheduled_cr_2)
    commit_service.commit(admin_user)
    commit_service = ChangeRequestCommitService(scheduled_cr_1)
    commit_service.commit(admin_user)

    # and move time on to after the feature states from both CRs should have gone live
    freezer.move_to(three_hours_from_now)

    # Then
    # the feature state in the latest scheduled cr should be the one that is returned
    feature_states = get_environment_flags_list(environment=environment)
    assert len(feature_states) == 1
    assert feature_states[0] == cr_2_fs


@pytest.mark.freeze_time(now)
def test_commit_change_request_publishes_environment_feature_versions(  # type: ignore[no-untyped-def]
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
    commit_service = ChangeRequestCommitService(change_request)
    environment_feature_version = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )
    environment_feature_version.feature_states.add(
        feature_state.clone(env=environment, as_draft=True)
    )

    change_request.environment_feature_versions.add(environment_feature_version)

    mock_rebuild_environment_document_task = mocker.patch(
        "core.workflows_services.rebuild_environment_document"
    )
    mock_trigger_update_version_webhooks = mocker.patch(
        "core.workflows_services.trigger_update_version_webhooks"
    )

    # When
    commit_service.commit(admin_user)

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


def test_publishing_segments_as_part_of_commit(
    segment: Segment,
    change_request: ChangeRequest,
    admin_user: FFAdminUser,
) -> None:
    # Given
    assert segment.version == 2
    cloner = SegmentCloneService(segment)
    cr_segment = cloner.shallow_clone("Test Name", "Test Description", change_request)
    assert cr_segment.rules.count() == 0

    # Add some rules that the original segment will be cloning from
    parent_rule = SegmentRule.objects.create(
        segment=cr_segment, type=SegmentRule.ALL_RULE
    )

    child_rule1 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.ANY_RULE
    )
    child_rule2 = SegmentRule.objects.create(
        rule=parent_rule, type=SegmentRule.NONE_RULE
    )
    Condition.objects.create(
        rule=child_rule1,
        property="child_rule1",
        operator=EQUAL,
        value="condition1",
        created_with_segment=True,
    )
    Condition.objects.create(
        rule=child_rule2,
        property="child_rule2",
        operator=PERCENTAGE_SPLIT,
        value="0.2",
        created_with_segment=False,
    )
    commit_service = ChangeRequestCommitService(change_request)
    # When
    commit_service.commit(admin_user)

    # Then
    segment.refresh_from_db()
    assert segment.version == 3
    assert segment.name == "Test Name"
    assert segment.description == "Test Description"
    assert segment.rules.count() == 1
    parent_rule2 = segment.rules.first()
    assert parent_rule2.type == SegmentRule.ALL_RULE  # type: ignore[union-attr]
    assert parent_rule2.rules.count() == 2  # type: ignore[union-attr]
    child_rule3, child_rule4 = list(parent_rule2.rules.all())  # type: ignore[union-attr]
    assert child_rule3.type == SegmentRule.ANY_RULE
    assert child_rule4.type == SegmentRule.NONE_RULE
    assert child_rule3.conditions.count() == 1
    assert child_rule4.conditions.count() == 1
    condition1 = child_rule3.conditions.first()
    condition2 = child_rule4.conditions.first()
    assert condition1.value == "condition1"
    assert condition2.value == "0.2"


def test_commit_change_request_does_not_fail_when_no_previous_feature_state(
    mocker: MockerFixture,
    environment: Environment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    mock_trigger = mocker.patch(
        "core.workflows_services.trigger_feature_state_change_webhooks"
    )

    mocker.patch(
        "features.models.FeatureState.objects.get_live_feature_states",
        return_value=FeatureState.objects.none(),
    )

    feature = Feature.objects.create(
        name="new_flag_without_history", project=environment.project
    )

    change_request = ChangeRequest.objects.create(
        environment=environment,
        title="Test No History CR",
        user=admin_user,
    )

    FeatureState.objects.create(
        feature=feature,
        environment=environment,
        change_request=change_request,
        enabled=True,
        version=None,
    )

    commit_service = ChangeRequestCommitService(change_request)

    # When
    commit_service.commit(committed_by=admin_user)

    # Then
    assert change_request.is_committed
    mock_trigger.assert_not_called()
