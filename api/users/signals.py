import warnings

from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.urls import reverse

from .models import FFAdminUser


@receiver(post_migrate, sender=FFAdminUser)
def warn_insecure(sender, **kwargs):
    if FFAdminUser.objects.count() == 0:
        path = reverse("api-v1:users:config-init")
        warnings.warn(
            f"YOUR INSTALLATION IS INSECURE: PLEASE ACCESS http://<your-server-domain:8000>{path} TO CREATE A SUPER USER"
        )
