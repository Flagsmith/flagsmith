from django.db import models

from users.models import FFAdminUser


class UserPasswordResetRequest(models.Model):
    user = models.ForeignKey(
        FFAdminUser, related_name="password_reset_requests", on_delete=models.CASCADE
    )
    requested_at = models.DateTimeField(auto_now_add=True)
