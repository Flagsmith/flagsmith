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
def cleanup_stale_oauth2_applications() -> None:
    """Remove DCR applications that were never used to obtain a token.

    An application is considered stale if it was registered more than 14 days
    ago and has no associated access tokens, refresh tokens, or grants.
    """
    from django.db.models import Exists, OuterRef
    from oauth2_provider.models import AccessToken, Application, Grant, RefreshToken

    threshold = timezone.now() - timedelta(days=14)
    stale = Application.objects.filter(
        created__lt=threshold,
        user__isnull=True,  # Only DCR-created apps (no user)
    ).exclude(
        Exists(AccessToken.objects.filter(application=OuterRef("pk")))
        | Exists(RefreshToken.objects.filter(application=OuterRef("pk")))
        | Exists(Grant.objects.filter(application=OuterRef("pk")))
    )
    count, _ = stale.delete()
    if count:
        logger.info("OAuth2 DCR cleanup: removed %d stale application(s).", count)
