from django.contrib.auth.forms import UserChangeForm
from django.forms import HiddenInput, fields


class CustomUserAdminForm(UserChangeForm):
    username = fields.CharField(required=False, widget=HiddenInput)
