import inspect
from datetime import date

from django import forms
from django.conf import settings
from django.core.mail import send_mail

from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation
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
