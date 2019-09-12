# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from organisations.chargebee import get_max_seats_for_plan


@python_2_unicode_compatible
class Organisation(models.Model):
    name = models.CharField(max_length=2000)
    has_requested_features = models.BooleanField(default=False)
    webhook_notification_email = models.EmailField(null=True, blank=True)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Org %s" % self.name

    def get_unique_slug(self):
        return str(self.id) + "-" + self.name

    @property
    def num_seats(self):
        return self.users.count()

    def has_subscription(self):
        return hasattr(self, 'subscription')


class Subscription(models.Model):
    organisation = models.OneToOneField(Organisation, on_delete=models.CASCADE, related_name='subscription')
    subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_date = models.DateField(blank=True, null=True)
    paid_subscription = models.BooleanField(default=False)
    free_to_use_subscription = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, null=True, blank=True)
    pending_cancellation = models.BooleanField(default=False)
    max_seats = models.IntegerField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.plan and not self.max_seats:
            self.max_seats = get_max_seats_for_plan(self.plan)
        super(Subscription, self).save(*args, **kwargs)


