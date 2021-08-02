import warnings

from django.urls import reverse


def warn_insecure(sender, **kwargs):
    from .models import FFAdminUser

    if FFAdminUser.objects.count() == 0:
        path = reverse("api-v1:users:config-init")
        warnings.warn(
            f"YOUR INSTALLATION IS INSECURE: PLEASE ACCESS http://<your-server-domain:8000>{path} TO CREATE A SUPER USER",
            RuntimeWarning,
        )
