from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import FFAdminUser


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = FFAdminUser
        fields = ('organisations',)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = FFAdminUser
        fields = ('organisations',)
