import inspect
from datetime import date

from django import forms
from django.conf import settings
from django.core.mail import send_mail

from environments.models import Environment
from features.models import Feature
from features.versioning.constants import DEFAULT_VERSION_LIMIT_DAYS
from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from organisations.subscriptions.constants import (
    FREE_PLAN_ID,
    MAX_API_CALLS_IN_FREE_PLAN,
    MAX_SEATS_IN_FREE_PLAN,
    TRIAL_SUBSCRIPTION_ID,
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


class StartTrialForm(forms.Form):
    max_seats = forms.IntegerField()
    max_api_calls = forms.IntegerField()

    def save(self, organisation: Organisation, commit: bool = True) -> Organisation:
        subscription = organisation.subscription

        subscription.max_seats = self.cleaned_data["max_seats"]
        subscription.max_api_calls = self.cleaned_data["max_api_calls"]
        subscription.subscription_id = TRIAL_SUBSCRIPTION_ID
        subscription.customer_id = TRIAL_SUBSCRIPTION_ID
        subscription.plan = "enterprise-saas-monthly-v2"

        OrganisationSubscriptionInformationCache.objects.update_or_create(
            organisation=organisation,
            defaults={
                "allowed_seats": self.cleaned_data["max_seats"],
                "allowed_30d_api_calls": self.cleaned_data["max_api_calls"],
                "allowed_projects": None,
                "audit_log_visibility_days": None,
                "feature_history_visibility_days": None,
            },
        )

        if commit:
            subscription.save()

        return organisation


class EndTrialForm(forms.Form):
    def save(self, organisation: Organisation, commit: bool = True) -> Organisation:
        subscription = organisation.subscription

        subscription.max_seats = MAX_SEATS_IN_FREE_PLAN
        subscription.max_api_calls = MAX_API_CALLS_IN_FREE_PLAN
        subscription.subscription_id = ""
        subscription.customer_id = ""
        subscription.plan = FREE_PLAN_ID
        subscription.save()

        OrganisationSubscriptionInformationCache.objects.update_or_create(
            organisation=organisation,
            defaults={
                "allowed_seats": MAX_SEATS_IN_FREE_PLAN,
                "allowed_30d_api_calls": MAX_API_CALLS_IN_FREE_PLAN,
                "allowed_projects": 1,
                "audit_log_visibility_days": 0,
                "feature_history_visibility_days": DEFAULT_VERSION_LIMIT_DAYS,
            },
        )

        if commit:
            subscription.save()

        return organisation


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
