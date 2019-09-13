from django.db.models.signals import pre_save
from django.dispatch import receiver

from organisations.chargebee import get_max_seats_for_plan
from .models import Subscription


@receiver(pre_save, sender=Subscription)
def update_max_seats_if_plan_changed(sender, instance, *args, **kwargs):
    new_object = False
    obj = None

    try:
        obj = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        new_object = True

    if instance.plan and (new_object or obj.plan != instance.plan or not instance.max_seats):
        instance.max_seats = get_max_seats_for_plan(instance.plan)
