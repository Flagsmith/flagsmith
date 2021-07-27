import warnings

from django.apps import AppConfig
from django.urls import reverse


class AuthenticationConfig(AppConfig):
    name = "users"

    def ready(self):

        from .models import FFAdminUser

        if FFAdminUser.objects.count() == 0:

            path = reverse("api-v1:users:config-init")
            warnings.warn(
                f"YOUR INSTALLATION IS INSECURE: PLEASE ACCESS http://<your-server-domain:8000>{path} TO CREATE A SUPER USER"
            )
