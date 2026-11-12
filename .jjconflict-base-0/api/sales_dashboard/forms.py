from django import forms

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


class MaxSeatsForm(forms.Form):
    max_seats = forms.IntegerField()

    def save(self, organisation, commit=True):  # type: ignore[no-untyped-def]
        organisation.subscription.max_seats = self.cleaned_data["max_seats"]
        organisation.subscription.save()


class MaxAPICallsForm(forms.Form):
    max_api_calls = forms.IntegerField()

    def save(self, organisation, commit=True):  # type: ignore[no-untyped-def]
        organisation.subscription.max_api_calls = self.cleaned_data["max_api_calls"]
        organisation.subscription.save()


class StartTrialForm(forms.Form):
    max_seats = forms.IntegerField()
    max_api_calls = forms.IntegerField()

    def save(self, organisation: Organisation, commit: bool = True) -> Organisation:
        subscription = organisation.subscription

        max_seats = self.cleaned_data["max_seats"]
        max_api_calls = self.cleaned_data["max_api_calls"]

        subscription.max_seats = max_seats
        subscription.max_api_calls = max_api_calls
        subscription.subscription_id = TRIAL_SUBSCRIPTION_ID
        subscription.customer_id = TRIAL_SUBSCRIPTION_ID
        subscription.plan = "enterprise-saas-monthly-v2"

        osic = getattr(
            organisation, "subscription_information_cache", None
        ) or OrganisationSubscriptionInformationCache(organisation=organisation)
        osic.upgrade_to_enterprise(seats=max_seats, api_calls=max_api_calls)

        if commit:
            subscription.save()
            osic.save()

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

        osic = getattr(
            organisation, "subscription_information_cache", None
        ) or OrganisationSubscriptionInformationCache(organisation=organisation)
        osic.reset_to_defaults()

        if commit:
            subscription.save()
            osic.save()

        return organisation
