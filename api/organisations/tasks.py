import logging
from datetime import timedelta

from app_analytics.influxdb_wrapper import get_current_api_usage
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Max
from django.template.loader import render_to_string
from django.utils import timezone

from integrations.flagsmith.client import get_client
from organisations import subscription_info_cache
from organisations.models import (
    APILimitAccessBlock,
    OranisationAPIUsageNotification,
    Organisation,
    OrganisationRole,
    Subscription,
)
from organisations.subscriptions.constants import FREE_PLAN_ID
from organisations.subscriptions.subscription_service import (
    get_subscription_metadata,
)
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from users.models import FFAdminUser

from .constants import (
    ALERT_EMAIL_MESSAGE,
    ALERT_EMAIL_SUBJECT,
    API_USAGE_ALERT_THRESHOLDS,
    API_USAGE_GRACE_PERIOD,
)
from .subscriptions.constants import SubscriptionCacheEntity

logger = logging.getLogger(__name__)


@register_task_handler()
def send_org_over_limit_alert(organisation_id) -> None:
    organisation = Organisation.objects.get(id=organisation_id)

    subscription_metadata = get_subscription_metadata(organisation)
    FFAdminUser.send_alert_to_admin_users(
        subject=ALERT_EMAIL_SUBJECT,
        message=ALERT_EMAIL_MESSAGE
        % (
            str(organisation.name),
            organisation.num_seats,
            subscription_metadata.seats,
            organisation.subscription.plan,
        ),
    )


@register_task_handler()
def send_org_subscription_cancelled_alert(
    organisation_name: str,
    formatted_cancellation_date: str,
) -> None:
    FFAdminUser.send_alert_to_admin_users(
        subject=f"Organisation {organisation_name} has cancelled their subscription",
        message=f"Organisation {organisation_name} has cancelled their subscription on {formatted_cancellation_date}",
    )


@register_task_handler()
def update_organisation_subscription_information_influx_cache():
    subscription_info_cache.update_caches((SubscriptionCacheEntity.INFLUX,))


@register_task_handler()
def update_organisation_subscription_information_cache() -> None:
    subscription_info_cache.update_caches(
        (SubscriptionCacheEntity.CHARGEBEE, SubscriptionCacheEntity.INFLUX)
    )


@register_recurring_task(
    run_every=timedelta(hours=12),
)
def finish_subscription_cancellation() -> None:
    now = timezone.now()
    previously = now + timedelta(hours=-24)
    for subscription in Subscription.objects.filter(
        cancellation_date__lt=now,
        cancellation_date__gt=previously,
    ):
        subscription.organisation.cancel_users()
        subscription.save_as_free_subscription()


def send_admin_api_usage_notification(
    organisation: Organisation, matched_threshold: int
) -> None:
    """
    Send notification to admins that the API has breached a threshold.
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

    OranisationAPIUsageNotification.objects.create(
        organisation=organisation,
        percent_usage=matched_threshold,
        notified_at=timezone.now(),
    )


def _handle_api_usage_notifications(organisation: Organisation) -> None:
    subscription_cache = organisation.subscription_information_cache
    billing_starts_at = subscription_cache.current_billing_term_starts_at
    now = timezone.now()

    # Truncate to the closest active month to get start of current period.
    month_delta = relativedelta(now, billing_starts_at).months
    period_starts_at = relativedelta(months=month_delta) + billing_starts_at

    days = relativedelta(now, period_starts_at).days
    api_usage = get_current_api_usage(organisation.id, f"{days}d")

    api_usage_percent = int(100 * api_usage / subscription_cache.allowed_30d_api_calls)

    matched_threshold = None
    for threshold in API_USAGE_ALERT_THRESHOLDS:
        if threshold > api_usage_percent:
            break

        matched_threshold = threshold

    # Didn't match even the lowest threshold, so no notification.
    if matched_threshold is None:
        return

    if OranisationAPIUsageNotification.objects.filter(
        notified_at__gt=period_starts_at,
        percent_usage=matched_threshold,
    ).exists():
        # Already sent the max notification level so don't resend.
        return

    send_admin_api_usage_notification(organisation, matched_threshold)


def handle_api_usage_notifications() -> None:
    flagsmith_client = get_client("local", local_eval=True)

    for organisation in Organisation.objects.filter(
        subscription_information_cache__current_billing_term_starts_at__isnull=False,
        subscription_information_cache__current_billing_term_ends_at__isnull=False,
    ).select_related(
        "subscription_information_cache",
    ):
        feature_enabled = flagsmith_client.get_identity_flags(
            f"org.{organisation.id}.{organisation.name}",
            traits={"organisation_id": organisation.id},
        ).is_feature_enabled("api_usage_alerting")
        if not feature_enabled:
            continue

        try:
            _handle_api_usage_notifications(organisation)
        except RuntimeError:
            logger.error(
                f"Error processing api usage for organisation {organisation.id}",
                exc_info=True,
            )


def restrict_use_due_to_api_limit_grace_period_over() -> None:
    """
    Restrict API use once a grace period has ended.

    Since free plans don't have predefined subscription periods, we
    use a rolling thirty day period to filter them.
    """

    grace_period = timezone.now() - timedelta(days=API_USAGE_GRACE_PERIOD)
    month_start = timezone.now() - timedelta(30)
    queryset = (
        OranisationAPIUsageNotification.objects.filter(
            notified_at__gt=month_start,
            notified_at__lt=grace_period,
            percent_usage__gte=100,
        )
        .values("organisation")
        .annotate(max_value=Max("percent_usage"))
    )

    organisation_ids = []
    for result in queryset:
        organisation_ids.append(result["organisation"])
    organisations = Organisation.objects.filter(
        id__in=organisation_ids,
        subscription__plan=FREE_PLAN_ID,
        api_limit_access_block__isnull=True,
    ).exclude(
        stop_serving_flags=True,
        block_access_to_admin=True,
    )

    update_organisations = []
    api_limit_access_blocks = []
    flagsmith_client = get_client("local", local_eval=True)

    for organisation in organisations:
        flags = flagsmith_client.get_identity_flags(
            f"org.{organisation.id}.{organisation.name}",
            traits={"organisation_id": organisation.id},
        )

        stop_serving = flags.is_feature_enabled("api_limiting_stop_serving_flags")
        block_access = flags.is_feature_enabled("api_limiting_block_access_to_admin")

        if not stop_serving and not block_access:
            continue

        organisation.stop_serving_flags = stop_serving
        organisation.block_access_to_admin = block_access

        api_limit_access_blocks.append(APILimitAccessBlock(organisation=organisation))
        update_organisations.append(organisation)

    APILimitAccessBlock.objects.bulk_create(api_limit_access_blocks)

    Organisation.objects.bulk_update(
        update_organisations, ["stop_serving_flags", "block_access_to_admin"]
    )


def unrestrict_after_api_limit_grace_period_is_stale() -> None:
    """
    This task handles accounts that have breached the API limit
    and have become restricted by setting the stop_serving_flags
    and block_access_to_admin to True. This task looks to find
    which accounts have started following the API limits in the
    latest rolling month and re-enables them if they no longer
    have recent API usage notifications.
    """

    month_start = timezone.now() - timedelta(30)
    still_restricted_organisation_notifications = (
        OranisationAPIUsageNotification.objects.filter(
            notified_at__gt=month_start,
            percent_usage__gte=100,
        )
        .values("organisation")
        .annotate(max_value=Max("percent_usage"))
    )
    still_restricted_organisation_ids = {
        q["organisation"] for q in still_restricted_organisation_notifications
    }
    organisation_ids = set(
        Organisation.objects.filter(
            api_limit_access_block__isnull=False,
        ).values_list("id", flat=True)
    )

    matching_organisations = Organisation.objects.filter(
        id__in=(organisation_ids - still_restricted_organisation_ids),
    )

    matching_organisations.update(stop_serving_flags=False, block_access_to_admin=False)

    for organisation in matching_organisations:
        organisation.api_limit_access_block.delete()


if settings.ENABLE_API_USAGE_ALERTING:
    register_recurring_task(
        run_every=timedelta(hours=12),
    )(handle_api_usage_notifications)
    register_recurring_task(
        run_every=timedelta(hours=12),
    )(restrict_use_due_to_api_limit_grace_period_over)
    register_recurring_task(
        run_every=timedelta(hours=12),
    )(unrestrict_after_api_limit_grace_period_is_stale)
