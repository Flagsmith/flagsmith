import warnings

from django.conf import settings
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.urls import reverse

from integrations.lead_tracking.pipedrive.lead_tracker import (
    PipedriveLeadTracker,
)
from users.models import FFAdminUser
from users.tasks import (
    create_pipedrive_lead,
    send_email_changed_notification_email,
)


@receiver(post_migrate, sender=FFAdminUser)
def warn_insecure(sender, **kwargs):
    if sender.objects.count() == 0:
        path = reverse("api-v1:users:config-init")
        warnings.warn(
            f"YOUR INSTALLATION IS INSECURE: PLEASE ACCESS http://<your-server-domain:8000>{path}"
            " TO CREATE A SUPER USER",
            RuntimeWarning,
        )


@receiver(post_save, sender=FFAdminUser)
def create_pipedrive_lead_signal(sender, instance, created, **kwargs):
    user: FFAdminUser = instance

    if not created:
        return False

    if not PipedriveLeadTracker.should_track(user):
        return

    create_pipedrive_lead.delay(args=(user.id,))


@receiver(post_save, sender=FFAdminUser)
def send_warning_email(sender, instance, created, **kwargs):
    send_email_changed_notification_email.delay(
        args=(
            instance.first_name,
            settings.DEFAULT_FROM_EMAIL,
            instance._initial_state["email"],
        )
    )
