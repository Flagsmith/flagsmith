from django.db.models.signals import pre_save
from django.dispatch import receiver

from organisations.chargebee import get_max_seats_for_plan, get_plan_id_from_subscription
from .models import Subscription


@receiver(pre_save, sender=Subscription)
def update_max_seats_if_plan_changed(sender, instance, *args, **kwargs):
    existing_object = None

    try:
        existing_object = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        pass

    if instance.subscription_id:
        current_plan = get_plan_id_from_subscription(instance.subscription_id)
        if not existing_object or current_plan != existing_object.plan:
            instance.max_seats = get_max_seats_for_plan(current_plan)
            instance.plan = current_plan
            instance.organisation.reset_alert_status()
