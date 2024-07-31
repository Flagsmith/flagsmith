import logging
from datetime import timedelta

from app_analytics.influxdb_wrapper import get_current_api_usage
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from organisations.models import (
    Organisation,
    OrganisationAPIUsageNotification,
    OrganisationRole,
)
from organisations.subscriptions.constants import MAX_API_CALLS_IN_FREE_PLAN
from users.models import FFAdminUser

from .constants import API_USAGE_ALERT_THRESHOLDS

logger = logging.getLogger(__name__)


def send_api_flags_blocked_notification(organisation: Organisation) -> None:
    recipient_list = FFAdminUser.objects.filter(
        userorganisation__organisation=organisation,
    )

    context = {"organisation": organisation}
    message = "organisations/api_flags_blocked_notification.txt"
    html_message = "organisations/api_flags_blocked_notification.html"

    send_mail(
        subject="Flagsmith API use has been blocked due to overuse",
        message=render_to_string(message, context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(recipient_list.values_list("email", flat=True)),
        html_message=render_to_string(html_message, context),
        fail_silently=True,
    )


def _send_api_usage_notification(
    organisation: Organisation, matched_threshold: int
) -> None:
    """
    Send notification to users that the API has breached a threshold.

    Only admins are included if the matched threshold is under
    100% of the API usage limits.
    """

    recipient_list = FFAdminUser.objects.filter(
        userorganisation__organisation=organisation,
    )

    if matched_threshold < 100:
        message = "organisations/api_usage_notification.txt"
        html_message = "organisations/api_usage_notification.html"

        # Since threshold < 100 only include admins.
        recipient_list = recipient_list.filter(
            userorganisation__role=OrganisationRole.ADMIN,
        )
    else:
        message = "organisations/api_usage_notification_limit.txt"
        html_message = "organisations/api_usage_notification_limit.html"

    context = {
        "organisation": organisation,
        "matched_threshold": matched_threshold,
    }

    send_mail(
        subject=f"Flagsmith API use has reached {matched_threshold}%",
        message=render_to_string(message, context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(recipient_list.values_list("email", flat=True)),
        html_message=render_to_string(html_message, context),
        fail_silently=True,
    )

    OrganisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=matched_threshold,
        notified_at=timezone.now(),
    )


def handle_api_usage_notification_for_organisation(organisation: Organisation) -> None:
    now = timezone.now()

    if organisation.subscription.is_free_plan:
        allowed_api_calls = organisation.subscription.max_api_calls
        # Default to a rolling month for free accounts
        days = 30
        period_starts_at = now - timedelta(days)
    elif not organisation.has_subscription_information_cache():
        # Since the calling code is a list of many organisations
        # log the error and return without raising an exception.
        logger.error(
            f"Paid organisation {organisation.id} is missing subscription information cache"
        )
        return
    else:
        subscription_cache = organisation.subscription_information_cache
        billing_starts_at = subscription_cache.current_billing_term_starts_at

        # Truncate to the closest active month to get start of current period.
        month_delta = relativedelta(now, billing_starts_at).months
        period_starts_at = relativedelta(months=month_delta) + billing_starts_at

        days = relativedelta(now, period_starts_at).days
        allowed_api_calls = subscription_cache.allowed_30d_api_calls

    api_usage = get_current_api_usage(organisation.id, f"-{days}d")

    # For some reason the allowed API calls is set to 0 so default to the max free plan.
    allowed_api_calls = allowed_api_calls or MAX_API_CALLS_IN_FREE_PLAN

    api_usage_percent = int(100 * api_usage / allowed_api_calls)

    matched_threshold = None
    for threshold in API_USAGE_ALERT_THRESHOLDS:
        if threshold > api_usage_percent:
            break

        matched_threshold = threshold

    # Didn't match even the lowest threshold, so no notification.
    if matched_threshold is None:
        return

    if OrganisationAPIUsageNotification.objects.filter(
        notified_at__gt=period_starts_at,
        percent_usage__gte=matched_threshold,
    ).exists():
        # Already sent the max notification level so don't resend.
        return

    _send_api_usage_notification(organisation, matched_threshold)
