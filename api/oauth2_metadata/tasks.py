import logging
from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone
from task_processor.decorators import register_recurring_task

logger = logging.getLogger(__name__)


@register_recurring_task(run_every=timedelta(hours=24))
def clear_expired_oauth2_tokens() -> None:
    call_command("cleartokens")


@register_recurring_task(run_every=timedelta(hours=24))
def log_new_oauth2_application_registrations() -> None:
    from oauth2_provider.models import Application

    since = timezone.now() - timedelta(hours=24)
    count: int = Application.objects.filter(created__gte=since).count()
    total: int = Application.objects.count()
    logger.info(
        "OAuth2 DCR monitoring: %d new application(s) registered in the last 24h "
        "(total: %d).",
        count,
        total,
    )


@register_recurring_task(run_every=timedelta(hours=24))
def cleanup_stale_oauth2_applications() -> None:
    """Remove DCR applications that were never used to obtain a token.

    An application is considered stale if it was registered more than 14 days
    ago and has no associated access tokens, refresh tokens, or grants.
    """
    from oauth2_provider.models import AccessToken, Application, Grant, RefreshToken

    threshold = timezone.now() - timedelta(days=14)
    stale = (
        Application.objects.filter(
            created__lt=threshold,
            user__isnull=True,  # Only DCR-created apps (no user)
        )
        .exclude(pk__in=AccessToken.objects.values("application_id"))
        .exclude(pk__in=RefreshToken.objects.values("application_id"))
        .exclude(pk__in=Grant.objects.values("application_id"))
    )
    count, _ = stale.delete()
    if count:
        logger.info("OAuth2 DCR cleanup: removed %d stale application(s).", count)
