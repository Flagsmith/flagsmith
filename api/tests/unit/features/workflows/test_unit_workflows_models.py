from datetime import timedelta

import pytest
from django.utils import timezone

from features.workflows.exceptions import ChangeRequestNotApprovedError
from features.workflows.models import ChangeRequestApproval
from users.models import FFAdminUser


def test_change_request_approve_by_required_approver(
    change_request_no_required_approvals, mocker
):
    # Given
    user = FFAdminUser.objects.create(email="approver@example.com")
    approval = ChangeRequestApproval.objects.create(
        user=user, change_request=change_request_no_required_approvals
    )
    now = timezone.now()
    mocker.patch("features.workflows.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.approve(user=user)

    # Then
    assert change_request_no_required_approvals.approvals.count() == 1
    approval.refresh_from_db()
    assert approval.approved_at == now
    assert approval.user == user


def test_change_request_approve_by_new_approver_when_no_approvals_exist(
    change_request_no_required_approvals, mocker
):
    # Given
    user = FFAdminUser.objects.create(email="approver@example.com")
    now = timezone.now()
    mocker.patch("features.workflows.models.timezone.now", return_value=now)

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
    mocker.patch("features.workflows.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.approve(user=user_2)

    # Then
    assert change_request_no_required_approvals.approvals.count() == 2

    approval.refresh_from_db()
    assert approval.approved_at is None

    assert change_request_no_required_approvals.approvals.filter(
        user=user_2, approved_at__isnull=False
    ).exists()


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
    mocker.patch("features.workflows.models.timezone.now", return_value=now)

    # When
    change_request_no_required_approvals.commit(committed_by=user)

    # Then
    assert change_request_no_required_approvals.committed_at == now
    assert change_request_no_required_approvals.committed_by == user

    assert change_request_no_required_approvals.feature_states.first().version == 2
    assert change_request_no_required_approvals.feature_states.first().live_from == now


def test_change_request_commit_scheduled(
    change_request_no_required_approvals,
    mocker,
):
    # Given
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    change_request_no_required_approvals.feature_states.update(live_from=tomorrow)

    user = FFAdminUser.objects.create(email="approver@example.com")

    mocker.patch("features.workflows.models.timezone.now", return_value=now)

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
