from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from custom_auth.models import UserPasswordResetRequest
from task_processor.decorators import register_recurring_task


@register_recurring_task(
    run_every=timedelta(seconds=settings.PASSWORD_RESET_EMAIL_COOLDOWN),
)
def clean_up_user_password_reset_request():
    UserPasswordResetRequest.objects.filter(
        requested_at__lt=timezone.now()
        - timedelta(seconds=settings.PASSWORD_RESET_EMAIL_COOLDOWN)
    ).delete()
