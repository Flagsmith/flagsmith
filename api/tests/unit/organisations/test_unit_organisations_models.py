from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from environments.models import Environment
from organisations.chargebee.metadata import ChargebeeObjMetadata
from organisations.models import (
    Organisation,
    OrganisationAPIUsageNotification,
    OrganisationSubscriptionInformationCache,
    Subscription,
)
from organisations.subscriptions.constants import (
    CHARGEBEE,
    FREE_PLAN_ID,
    FREE_PLAN_SUBSCRIPTION_METADATA,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    TRIAL_SUBSCRIPTION_ID,
    XERO,
    SubscriptionPlanFamily,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from organisations.subscriptions.metadata import BaseSubscriptionMetadata
from organisations.subscriptions.xero.metadata import XeroSubscriptionMetadata
from users.models import FFAdminUser


def test_organisation_has_paid_subscription_true(db: None) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id="subscription_id"
    )

    # refresh organisation to load subscription
    organisation.refresh_from_db()

    # Then
    assert organisation.has_paid_subscription()


@pytest.mark.parametrize(
    "plan_id, expected_has_enterprise",
    (
        ("free", False),
        ("enterprise", True),
        ("enterprise-semiannual", True),
        ("scale-up", False),
        ("scaleup", False),
        ("scale-up-v2", False),
        ("scale-up-v2-annual", False),
        ("startup", False),
        ("start-up", False),
        ("start-up-v2", False),
        ("start-up-v2-annual", False),
    ),
)
def test_organisation_has_enterprise_subscription(
    plan_id: str, expected_has_enterprise: bool, organisation: Organisation
) -> None:
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        plan=plan_id, subscription_id="subscription_id"
    )

    # # When
    organisation.refresh_from_db()

    # Then
    assert organisation.has_enterprise_subscription() is expected_has_enterprise


def test_organisation_has_paid_subscription_missing_subscription_id(db: None) -> None:
    # Given
    organisation = Organisation.objects.create(name="Test org")
    assert (
        Subscription.objects.filter(organisation=organisation).first().subscription_id
        is None
    )

    # Then
    assert not organisation.has_paid_subscription()


@mock.patch("organisations.models.cancel_chargebee_subscription")
def test_organisation_cancel_subscription_cancels_chargebee_subscription(  # type: ignore[no-untyped-def]
    mocked_cancel_chargebee_subscription,
    organisation: Organisation,
):
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id="subscription_id", payment_method=CHARGEBEE
    )
    subscription = Subscription.objects.get(organisation=organisation)

    # refresh organisation to load subscription
    organisation.refresh_from_db()

    # When
    organisation.cancel_subscription()

    # Then
    mocked_cancel_chargebee_subscription.assert_called_once_with(
        subscription.subscription_id
    )
    # refresh subscription object
    subscription.refresh_from_db()
    # Subscription has been immediately transformed to free.
    assert subscription.cancellation_date is None
    assert subscription.subscription_id is None
    assert subscription.billing_status is None
    assert subscription.payment_method is None
    assert subscription.plan == FREE_PLAN_ID


def test_organisation_rebuild_environment_document_on_stop_serving_flags_changed(  # type: ignore[no-untyped-def]
    environment: Environment, organisation: Organisation, mocker: MockerFixture
):
    # Given
    mocked_rebuild_environment_document = mocker.patch(
        "environments.tasks.rebuild_environment_document"
    )
    assert organisation.stop_serving_flags is False

    # When
    organisation.stop_serving_flags = True
    organisation.save()

    # Then
    mocked_rebuild_environment_document.delay.assert_called_once_with(
        args=(environment.id,)
    )


def test_organisation_rebuild_environment_document_on_stop_serving_flags_unchanged(  # type: ignore[no-untyped-def]
    environment: Environment, organisation: Organisation, mocker: MockerFixture
):
    # Given
    mocked_rebuild_environment_document = mocker.patch(
        "environments.tasks.rebuild_environment_document"
    )

    # When saving something irrelevant
    organisation.alerted_over_plan_limit = True
    organisation.save()

    # Then the task should not be called
    mocked_rebuild_environment_document.delay.assert_not_called()


def test_organisation_over_plan_seats_limit_returns_false_if_not_over_plan_seats_limit(  # type: ignore[no-untyped-def]  # noqa: E501
    organisation, chargebee_subscription, mocker
):
    # Given
    seats = 200
    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        autospec=True,
        return_value=BaseSubscriptionMetadata(seats=seats),
    )
    # Then
    assert organisation.over_plan_seats_limit() is False
    mocked_get_subscription_metadata.assert_called_once_with(chargebee_subscription)


def test_organisation_over_plan_seats_limit_returns_true_if_over_plan_seats_limit(  # type: ignore[no-untyped-def]
    organisation, chargebee_subscription, mocker, admin_user
):
    # Given
    seats = 0
    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        autospec=True,
        return_value=BaseSubscriptionMetadata(seats=seats),
    )
    # Then
    assert organisation.over_plan_seats_limit() is True
    mocked_get_subscription_metadata.assert_called_once_with(chargebee_subscription)


def test_organisation_over_plan_seats_no_subscription(organisation, mocker, admin_user):  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    organisation.subscription.max_seats = 0
    organisation.subscription.save()

    mocked_get_subscription_metadata = mocker.patch(
        "organisations.models.Subscription.get_subscription_metadata",
        autospec=True,
    )
    # Then
    assert organisation.over_plan_seats_limit() is True
    mocked_get_subscription_metadata.assert_not_called()


@pytest.mark.saas_mode
def test_organisation_is_auto_seat_upgrade_available(
    organisation: Organisation,
) -> None:
    # Given
    plan = "Scale-Up"
    subscription_id = "subscription-id"

    Subscription.objects.filter(organisation=organisation).update(
        subscription_id=subscription_id, plan=plan
    )

    # refresh organisation to load subscription
    organisation.refresh_from_db()

    # Then
    assert organisation.is_auto_seat_upgrade_available() is True


def test_organisation_default_subscription_have_one_max_seat(
    organisation: Organisation,
) -> None:
    # Given
    subscription = Subscription.objects.get(organisation=organisation)

    # Then
    assert subscription.max_seats == 1


def test_organisation_is_paid_returns_false_if_subscription_does_not_exists(db):  # type: ignore[no-untyped-def]
    # Given
    organisation = Organisation.objects.create(name="Test org")
    # Then
    assert organisation.is_paid is False


def test_organisation_is_paid_returns_true_if_active_subscription_exists(  # type: ignore[no-untyped-def]
    organisation, chargebee_subscription
):
    # When/Then
    assert organisation.is_paid is True


def test_organisation_is_paid_returns_false_if_cancelled_subscription_exists(  # type: ignore[no-untyped-def]
    organisation, chargebee_subscription
):
    # Given
    organisation = Organisation.objects.create(name="Test org")
    chargebee_subscription.cancellation_date = datetime.now()
    chargebee_subscription.save()

    # Then
    assert organisation.is_paid is False


def test_organisation_subscription_get_subscription_metadata_returns_cb_metadata_for_cb_subscription(  # type: ignore[no-untyped-def]  # noqa: E501
    organisation: Organisation,
    mocker: MockerFixture,
    settings: SettingsWrapper,
):
    # Given
    seats = 10
    api_calls = 50000000
    projects = 10

    settings.VERSIONING_RELEASE_DATE = timezone.now() - timedelta(days=1)

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=seats,
        allowed_30d_api_calls=api_calls,
        allowed_projects=projects,
    )
    expected_metadata = ChargebeeObjMetadata(
        seats=seats, api_calls=api_calls, projects=projects
    )
    mocker.patch("organisations.models.is_saas", return_value=True)
    Subscription.objects.filter(organisation=organisation).update(
        plan="scale-up-v2",
        subscription_id="subscription-id",
        payment_method=CHARGEBEE,
    )
    organisation.subscription.refresh_from_db()

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == expected_metadata


def test_get_subscription_metadata_returns_unlimited_values_for_audit_and_versions_when_released(  # type: ignore[no-untyped-def]  # noqa: E501
    organisation: Organisation,
    mocker: MockerFixture,
    settings: SettingsWrapper,
):
    # Given
    seats = 10
    api_calls = 50000000
    projects = 10
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    two_days_ago = now - timedelta(days=2)

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=seats,
        allowed_30d_api_calls=api_calls,
        allowed_projects=projects,
        # values from here should be overridden
        audit_log_visibility_days=30,
        feature_history_visibility_days=30,
    )
    expected_metadata = ChargebeeObjMetadata(
        seats=seats,
        api_calls=api_calls,
        projects=projects,
        # the following values are patched on based on the
        # VERSIONING_RELEASE_DATE setting
        audit_log_visibility_days=None,
        feature_history_visibility_days=None,
    )
    mocker.patch("organisations.models.is_saas", return_value=True)
    Subscription.objects.filter(organisation=organisation).update(
        plan="scale-up-v2",
        subscription_id="subscription-id",
        payment_method=CHARGEBEE,
        subscription_date=two_days_ago,
    )
    organisation.subscription.refresh_from_db()

    settings.VERSIONING_RELEASE_DATE = yesterday

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == expected_metadata


def test_organisation_subscription_get_subscription_metadata_returns_xero_metadata_for_xero_sub(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker: MockerFixture,
):
    # Given
    subscription = Subscription(
        payment_method=XERO, subscription_id="xero-subscription", plan="enterprise"
    )
    expected_metadata = XeroSubscriptionMetadata(
        seats=subscription.max_seats, api_calls=subscription.max_api_calls
    )
    mocker.patch("organisations.models.is_saas", return_value=True)

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == expected_metadata


def test_organisation_subscription_get_subscription_metadata_returns_free_plan_metadata_for_no_plan():  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    subscription = Subscription()

    # When
    subscription_metadata = subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == FREE_PLAN_SUBSCRIPTION_METADATA


@pytest.mark.parametrize(
    "subscription_id, plan, max_seats, max_api_calls, expected_seats, "
    "expected_api_calls, expected_projects",
    (
        (
            None,
            "free",
            10,
            5000000,
            MAX_SEATS_IN_FREE_PLAN,
            MAX_API_CALLS_IN_FREE_PLAN,
            settings.MAX_PROJECTS_IN_FREE_PLAN,
        ),
        ("anything", "enterprise", 20, 5000000, 20, 5000000, None),
        (TRIAL_SUBSCRIPTION_ID, "enterprise", 20, 5000000, 20, 5000000, None),
    ),
)
def test_organisation_get_subscription_metadata_for_manually_added_enterprise_saas_licenses(
    organisation: Organisation,
    subscription_id: str | None,
    plan: str,
    max_seats: int,
    max_api_calls: int,
    expected_seats: int,
    expected_api_calls: int,
    expected_projects: int | None,
    mocker: MockerFixture,
) -> None:
    """
    Specific test to make sure that we can manually add subscriptions to
    the SaaS platform and the values stored in the Django database will
    be correctly used.
    """
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        subscription_id=subscription_id,
        plan=plan,
        max_seats=max_seats,
        max_api_calls=max_api_calls,
    )
    organisation.subscription.refresh_from_db()
    mocker.patch("organisations.models.is_saas", return_value=True)

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata.projects == expected_projects
    assert subscription_metadata.seats == expected_seats
    assert subscription_metadata.api_calls == expected_api_calls


def test_organisation_get_subscription_metadata_for_self_hosted_open_source(
    organisation: Organisation, mocker: MockerFixture
) -> None:
    """
    Open source should ignore the details provided in the
    subscription and always return the free plan metadata.
    """
    # Given
    Subscription.objects.filter(organisation=organisation).update(
        max_seats=100,
        max_api_calls=10000000000,
        plan="enterprise",
        subscription_id="subscription-id",
    )
    organisation.subscription.refresh_from_db()
    mocker.patch("organisations.models.is_enterprise", return_value=False)
    mocker.patch("organisations.models.is_saas", return_value=False)

    # When
    subscription_metadata = organisation.subscription.get_subscription_metadata()

    # Then
    assert subscription_metadata == FREE_PLAN_SUBSCRIPTION_METADATA


@pytest.mark.saas_mode
def test_organisation_subscription_add_single_seat_calls_correct_chargebee_method_for_upgradable_plan(  # noqa: E501
    mocker: MockerFixture,
) -> None:
    # Given
    subscription_id = "subscription-id"
    subscription = Subscription(subscription_id=subscription_id, plan="scale-up")

    mocked_add_single_seat = mocker.patch(
        "organisations.models.add_single_seat", autospec=True
    )
    # When
    subscription.add_single_seat()  # type: ignore[no-untyped-call]

    # Then
    mocked_add_single_seat.assert_called_once_with(subscription_id)


def test_organisation_subscription_add_single_seat_raises_error_for_non_upgradable_plan(  # noqa: E501
    mocker: MockerFixture,
) -> None:
    # Given
    subscription_id = "subscription-id"
    subscription = Subscription(
        subscription_id=subscription_id, plan="not-a-scale-up-plan"
    )

    mocked_add_single_seat = mocker.patch(
        "organisations.models.add_single_seat", autospec=True
    )

    # When
    with pytest.raises(SubscriptionDoesNotSupportSeatUpgrade):
        subscription.add_single_seat()  # type: ignore[no-untyped-call]

    # and add_single_seat was not called
    mocked_add_single_seat.assert_not_called()


def test_organisation_update_clears_environment_caches(  # type: ignore[no-untyped-def]
    mocker, organisation, environment
):
    # Given
    mock_environment_cache = mocker.patch("organisations.models.environment_cache")

    # When
    organisation.name += "update"
    organisation.save()

    # Then
    mock_environment_cache.delete_many.assert_called_once_with([environment.api_key])


def test_reset_of_api_notifications(organisation: Organisation) -> None:
    # Given
    now = timezone.now()
    osic = OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        allowed_seats=10,
        allowed_projects=3,
        allowed_30d_api_calls=100,
        chargebee_email="test@example.com",
        current_billing_term_starts_at=now - timedelta(days=45),
        current_billing_term_ends_at=now + timedelta(days=320),
    )

    # Create a notification which should be deleted shortly.
    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=90,
        notified_at=now,
    )

    # Keep a notification which should not be deleted.
    organisation2 = Organisation.objects.create(name="Test org2")
    oapiun = OrganisationAPIUsageNotification.objects.create(
        organisation=organisation2,
        percent_usage=90,
        notified_at=now,
    )

    # When
    osic.allowed_30d_api_calls *= 2
    osic.save()

    # Then
    assert OrganisationAPIUsageNotification.objects.count() == 1
    assert OrganisationAPIUsageNotification.objects.first() == oapiun


def test_organisation_creates_subscription_cache(
    db: None, mocker: MockerFixture
) -> None:
    # Given
    mocker.patch("organisations.models.is_saas", return_value=True)

    # When
    organisation = Organisation.objects.create(name="Test org")

    # Then
    assert organisation.subscription_information_cache
    assert (
        organisation.subscription_information_cache.allowed_seats
        == MAX_SEATS_IN_FREE_PLAN
    )
    assert (
        organisation.subscription_information_cache.allowed_30d_api_calls
        == MAX_API_CALLS_IN_FREE_PLAN
    )


@pytest.mark.parametrize(
    "plan_id, expected_plan_family",
    (
        ("free", SubscriptionPlanFamily.FREE),
        ("enterprise", SubscriptionPlanFamily.ENTERPRISE),
        ("enterprise-semiannual", SubscriptionPlanFamily.ENTERPRISE),
        ("scale-up", SubscriptionPlanFamily.SCALE_UP),
        ("scaleup", SubscriptionPlanFamily.SCALE_UP),
        ("scale-up-v2", SubscriptionPlanFamily.SCALE_UP),
        ("scale-up-v2-annual", SubscriptionPlanFamily.SCALE_UP),
        ("startup", SubscriptionPlanFamily.START_UP),
        ("start-up", SubscriptionPlanFamily.START_UP),
        ("start-up-v2", SubscriptionPlanFamily.START_UP),
        ("start-up-v2-annual", SubscriptionPlanFamily.START_UP),
    ),
)
def test_subscription_plan_family(
    plan_id: str, expected_plan_family: SubscriptionPlanFamily
) -> None:
    assert Subscription(plan=plan_id).subscription_plan_family == expected_plan_family


@pytest.mark.parametrize(
    "plan_id, expected_is_enterprise",
    (
        ("free", False),
        ("enterprise", True),
        ("enterprise-semiannual", True),
        ("scale-up", False),
        ("scaleup", False),
        ("scale-up-v2", False),
        ("scale-up-v2-annual", False),
        ("startup", False),
        ("start-up", False),
        ("start-up-v2", False),
        ("start-up-v2-annual", False),
    ),
)
def test_subscription_is_enterprise_property(
    plan_id: str, expected_is_enterprise: bool, organisation: Organisation
) -> None:
    # Given
    subscription = Subscription.objects.get(organisation=organisation)

    subscription.plan = plan_id
    subscription.save()

    # Then
    assert subscription.is_enterprise is expected_is_enterprise


@pytest.mark.parametrize(
    "billing_term_starts_at, billing_term_ends_at, expected_result",
    [
        (None, None, False),
        (
            timezone.now() - timedelta(hours=1),
            timezone.now() + timedelta(days=30),
            True,
        ),
        (
            timezone.now() - timedelta(days=30),
            timezone.now() + timedelta(hours=1),
            True,
        ),
        (
            timezone.now() - timedelta(days=30),
            timezone.now() - timedelta(days=5),
            False,
        ),
    ],
)
def test_organisation_has_billing_periods(
    organisation: Organisation,
    billing_term_starts_at: datetime,
    billing_term_ends_at: datetime,
    expected_result: bool,
) -> None:
    # Given
    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=billing_term_starts_at,
        current_billing_term_ends_at=billing_term_ends_at,
    )

    organisation.refresh_from_db()
    # When
    result = organisation.subscription.has_active_billing_periods

    # Then
    assert result == expected_result


@pytest.mark.freeze_time("2023-01-19T09:09:47+00:00")
def test_user_organisation_create_calls_hubspot_lead_tracking(
    mocker: MagicMock, db: None, settings: SettingsWrapper, organisation: Organisation
) -> None:
    # Given
    settings.ENABLE_HUBSPOT_LEAD_TRACKING = True
    track_hubspot_lead_v2 = mocker.patch("organisations.models.track_hubspot_lead_v2")

    user = FFAdminUser.objects.create(
        email="test@example.com", first_name="John", last_name="Doe"
    )

    # When
    user.add_organisation(organisation)

    # Then
    track_hubspot_lead_v2.delay.assert_called_once_with(
        args=(user.id, organisation.id),
        delay_until=timezone.now() + timedelta(minutes=3),
    )
