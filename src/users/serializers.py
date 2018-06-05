from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from rest_auth.registration.serializers import RegisterSerializer

from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _

from organisations.serializers import OrganisationSerializer
from .models import FFAdminUser, Invite


class UserFullSerializer(serializers.ModelSerializer):
    organisations = OrganisationSerializer(many=True)

    class Meta:
        model = FFAdminUser
        fields = ('id', 'email', 'first_name', 'last_name', 'organisations')


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = FFAdminUser
        fields = ('email', 'password')


class UserRegisterSerializer(RegisterSerializer):

    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)

    def validate_first_name(self, first_name):
        cleaned_first_name = first_name.strip()
        if first_name is None or first_name == "":
            raise serializers.ValidationError(
                _("First name cannot be empty")
            )
        return cleaned_first_name

    def validate_last_name(self, last_name):
        cleaned_last_name = last_name.strip()
        if last_name is None or last_name == "":
            raise serializers.ValidationError(
                _("Last name cannot be empty")
            )
        return cleaned_last_name

    def get_cleaned_data(self):
        return {
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', '')
        }

    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        setup_user_email(request, user, [])
        user.save()
        return user


class InviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invite
        fields = ('email', 'organisation', 'frontend_base_url', 'invited_by')
