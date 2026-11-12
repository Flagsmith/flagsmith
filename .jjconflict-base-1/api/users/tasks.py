from django.core.mail import send_mail
from django.template.loader import render_to_string
from task_processor.decorators import (
    register_task_handler,
)


@register_task_handler()
def send_email_changed_notification_email(  # type: ignore[no-untyped-def]
    first_name: str, from_email: str, original_email: str
):
    context = {
        "first_name": first_name,
    }

    send_mail(
        subject="Your Flagsmith email address has been changed",
        from_email=from_email,
        message=render_to_string("users/email_updated.txt", context),
        recipient_list=[original_email],
        fail_silently=True,
    )
