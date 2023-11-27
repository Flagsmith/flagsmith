import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import (
    Organisation,
    OrganisationRole,
    UserOrganisation,
)
from organisations.subscriptions.constants import (
    FREE_PLAN_ID,
    MAX_SEATS_IN_FREE_PLAN,
)
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from organisations.tasks import (
    ALERT_EMAIL_MESSAGE,
    ALERT_EMAIL_SUBJECT,
    finish_subscription_cancellation,
    send_org_over_limit_alert,
)
from users.models import FFAdminUser


def test_send_org_over_limit_alert_for_organisation_with_free_subscription(
    organisation, mocker
):
    # Given
    mocked_ffadmin_user = mocker.patch("organisations.tasks.FFAdminUser")

    # When
    send_org_over_limit_alert(organisation.id)

    # Then
    args, kwargs = mocked_ffadmin_user.send_alert_to_admin_users.call_args
    assert len(args) == 0
    assert len(kwargs) == 2
    assert kwargs["message"] == ALERT_EMAIL_MESSAGE % (
        organisation.name,
        organisation.num_seats,
        MAX_SEATS_IN_FREE_PLAN,
        FREE_PLAN_ID,
    )
    assert kwargs["subject"] == ALERT_EMAIL_SUBJECT


@pytest.mark.parametrize(
    "SubscriptionMetadata", [ChargebeeObjMetadata, XeroSubscriptionMetadata]
)
def test_send_org_over_limit_alert_for_organisation_with_subscription(
    organisation, subscription, mocker, SubscriptionMetadata
):
    # Given
    mocked_ffadmin_user = mocker.patch("organisations.tasks.FFAdminUser")
    max_seats = 10
    mocker.patch(
        "organisations.tasks.get_subscription_metadata",
        return_value=SubscriptionMetadata(seats=max_seats),
    )

    # When
    send_org_over_limit_alert(organisation.id)

    # Then
    args, kwargs = mocked_ffadmin_user.send_alert_to_admin_users.call_args
    assert len(args) == 0
    assert len(kwargs) == 2
    assert kwargs["message"] == ALERT_EMAIL_MESSAGE % (
        organisation.name,
        organisation.num_seats,
        max_seats,
        subscription.plan,
    )
    assert kwargs["subject"] == ALERT_EMAIL_SUBJECT


def test_finish_subscription_cancellation(db: None):
    organisation1 = Organisation.objects.create()
    organisation2 = Organisation.objects.create()
    organisation3 = Organisation.objects.create()
    organisation4 = Organisation.objects.create()

    # Far future cancellation will be unaffected.
    organisation_user_count = 3
    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation1,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )
    future = timezone.now() + timedelta(days=20)
    organisation1.subscription.cancel(cancellation_date=future)

    # Two organisations are impacted.
    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation2,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )

    organisation2.subscription.cancel(
        cancellation_date=timezone.now() - timedelta(hours=2)
    )

    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation3,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )
    organisation3.subscription.cancel(
        cancellation_date=timezone.now() - timedelta(hours=4)
    )

    # Remaining organisation4 has not canceled, should be left unaffected.
    for __ in range(organisation_user_count):
        UserOrganisation.objects.create(
            organisation=organisation4,
            user=FFAdminUser.objects.create(email=f"{uuid.uuid4()}@example.com"),
            role=OrganisationRole.ADMIN,
        )

    # When
    finish_subscription_cancellation()

    # Then
    organisation1.refresh_from_db()
    organisation2.refresh_from_db()
    organisation3.refresh_from_db()
    organisation4.refresh_from_db()

    assert organisation1.num_seats == organisation_user_count
    assert organisation2.num_seats == 1
    assert organisation3.num_seats == 1
    assert organisation4.num_seats == organisation_user_count
