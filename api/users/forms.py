from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserChangeForm
from django.contrib.sites.models import Site
from django.forms import HiddenInput, fields

from users.models import FFAdminUser


class CustomUserAdminForm(UserChangeForm):
    username = fields.CharField(required=False, widget=HiddenInput)


class InitConfigForm(forms.Form):
    username = forms.CharField(max_length=200)
    email = forms.EmailField()

    password = forms.CharField(max_length=32, widget=forms.PasswordInput)
    site_name = forms.CharField(
        max_length=50, help_text="A human-readable “verbose” name for the website"
    )
    site_domain = forms.CharField(
        max_length=100,
        help_text="The fully qualified domain name associated with the website. For example, www.example.com",
    )

    def create_admin(self):
        FFAdminUser.objects.create_superuser(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            username=self.cleaned_data["username"],
            is_active=True,
        )

    def update_site(self):
        Site.objects.filter(id=settings.SITE_ID).update(
            name=self.cleaned_data["site_name"], domain=self.cleaned_data["site_domain"]
        )
