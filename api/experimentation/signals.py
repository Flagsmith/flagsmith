from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from environments.models import Environment
from experimentation.services import ensure_flagsmith_warehouse_connection


@receiver(post_save, sender=Environment)
def auto_connect_warehouse_on_environment_create(
    sender: type[Environment],
    instance: Environment,
    created: bool,
    **kwargs: object,
) -> None:
    if not created:
        return
    ensure_flagsmith_warehouse_connection(instance)
