import inspect
from datetime import date

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404

from environments.models import Environment
from features.models import Feature
from organisations.chargebee import (
    get_subscription_metadata as get_subscription_metadata_from_chargebee,
)
from organisations.models import Organisation
from organisations.subscriptions.constants import CHARGEBEE
from organisations.subscriptions.subscription_service import (
    get_subscription_metadata,
)
from projects.models import Project
from users.models import FFAdminUser


class MaxSeatsForm(forms.Form):
    max_seats = forms.IntegerField()

    def save(self, organisation, commit=True):
        organisation.subscription.max_seats = self.cleaned_data["max_seats"]
        organisation.subscription.save()


class MaxAPICallsForm(forms.Form):
    max_api_calls = forms.IntegerField()

    def save(self, organisation, commit=True):
        organisation.subscription.max_api_calls = self.cleaned_data["max_api_calls"]
        organisation.subscription.save()


class EmailUsageForm(forms.Form):
    email_address = forms.EmailField()

    def save(self, commit=True):
        message = inspect.cleandoc(
            f"""
            Current Flagsmith Stats on {date.today()}:

            Total Organisations = {Organisation.objects.all().count()}
            Total Projects = {Project.objects.all().count()}
            Total Environments = {Environment.objects.all().count()}
            Total Features = {Feature.objects.all().count()}
            Total Seats = {FFAdminUser.objects.all().count()}
            """
        )

        send_mail(
            subject="Flagsmith Usage Report",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.cleaned_data["email_address"]],
            fail_silently=True,
        )


class ChargebeeSyncForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.organisation_id = kwargs.pop("organisation_id", None)
        super().__init__(*args, **kwargs)

    subscription_id = forms.CharField()

    def clean(self):
        if self._errors:
            raise forms.ValidationError("No subscription_id value")

        # Check the Chargebee Subscription ID exists and is valid
        metadata = get_subscription_metadata_from_chargebee(
            self.cleaned_data["subscription_id"]
        )
        if metadata is None:
            raise ValidationError("Could not find valid Subscription in Chargebee")

    def save(self, commit=True):
        subscription_id = self.cleaned_data["subscription_id"]

        organisation = get_object_or_404(
            Organisation.objects.select_related("subscription"), pk=self.organisation_id
        )

        organisation.subscription.subscription_id = subscription_id
        organisation.subscription.payment_method = CHARGEBEE
        organisation.save()

        subscription_metadata = get_subscription_metadata(organisation)
        organisation.update_chargebee_metadata(subscription_metadata)
