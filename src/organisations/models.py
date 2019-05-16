# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class Organisation(models.Model):
    name = models.CharField(max_length=2000)
    pending_cancellation = models.BooleanField(default=False)
    has_requested_features = models.BooleanField(default=False)
    webhook_notification_email = models.EmailField(null=True, blank=True)
    created_date = models.DateTimeField('DateCreated', auto_now_add=True)
    paid_subscription = models.BooleanField(default=False)
    free_to_use_subscription = models.BooleanField(default=True)
    plan = models.CharField(max_length=20, null=True, blank=True)
    subscription_date = models.DateTimeField('SubscriptionDate', blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return "Org %s" % self.name

    def get_unique_slug(self):
        return str(self.id) + "-" + self.name
