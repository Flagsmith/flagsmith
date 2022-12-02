import warnings

from django.conf import settings
from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.urls import reverse

from users.models import FFAdminUser
from users.tasks import create_pipedrive_lead


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
    if not (
        created
        and (settings.PIPEDRIVE_API_TOKEN or settings.ENABLE_PIPEDRIVE_LEAD_TRACKING)
    ):
        return

    create_pipedrive_lead.delay(args=(instance.id,))
