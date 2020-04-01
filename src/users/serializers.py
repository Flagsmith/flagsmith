from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from django.utils.translation import ugettext_lazy as _
from rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from organisations.models import Organisation
from organisations.serializers import UserOrganisationSerializer
from .models import FFAdminUser, Invite, UserPermissionGroup


class UserIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        organisation = Organisation.objects.get(pk=self.context.get('organisation'))
        user = self._get_user(validated_data)

        if user and organisation in user.organisations.all():
            user.remove_organisation(organisation)

        return user

    def validate(self, attrs):
        if not FFAdminUser.objects.filter(pk=attrs.get('id')).exists():
            message = 'User with id %d does not exist' % attrs.get('id')
            raise ValidationError({'id': message})
        return attrs

    def _get_user(self, validated_data):
        try:
            return FFAdminUser.objects.get(pk=validated_data.get('id'))
        except FFAdminUser.DoesNotExist:
            return None


class UserFullSerializer(serializers.ModelSerializer):
    organisations = UserOrganisationSerializer(source='userorganisation_set', many=True)

    class Meta:
        model = FFAdminUser
        fields = ('id', 'email', 'first_name', 'last_name', 'organisations')


class UserLoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = FFAdminUser
        fields = ('email', 'password')


class UserListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField(read_only=True)
    join_date = serializers.SerializerMethodField(read_only=True)

    default_fields = ('id', 'email', 'first_name', 'last_name')
    organisation_users_fields = ('role', 'date_joined')

    class Meta:
        model = FFAdminUser

    def get_field_names(self, declared_fields, info):
        fields = self.default_fields
        if self.context.get('organisation'):
            fields += self.organisation_users_fields
        return fields

    def get_role(self, instance):
        return instance.get_organisation_role(self.context.get('organisation'))

    def get_join_date(self, instance):
        return instance.get_organisation_join_date(self.context.get('organisation'))


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
        fields = ('email', 'organisation', 'frontend_base_url', 'invited_by', 'date_created')


class InviteListSerializer(serializers.ModelSerializer):
    invited_by = UserListSerializer()

    class Meta:
        model = Invite
        fields = ('id', 'email', 'date_created', 'invited_by')


class UserIdsSerializer(serializers.Serializer):
    user_ids = serializers.ListField(serializers.IntegerField)


class UserPermissionGroupSerializerList(serializers.ModelSerializer):
    class Meta:
        model = UserPermissionGroup
        fields = ('id', 'name', 'users')
        read_only_fields = ('id',)


class UserPermissionGroupSerializerDetail(UserPermissionGroupSerializerList):
    # TODO: remove users from here and just add a summary of number of users
    users = UserListSerializer(many=True, read_only=True)
