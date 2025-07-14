from abc import abstractmethod

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.db.models import F
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from integrations.lead_tracking.hubspot.services import (
    register_hubspot_tracker_and_track_user,
)
from users.auth_type import AuthType
from users.models import FFAdminUser, SignUpType
from users.serializers import UTMDataSerializer

from ..serializers import InviteLinkValidationMixin
from .github import GithubUser
from .google import get_user_info

GOOGLE_URL = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&"
UserModel = get_user_model()


class OAuthLoginSerializer(InviteLinkValidationMixin, serializers.Serializer):  # type: ignore[type-arg]
    access_token = serializers.CharField(
        required=True,
        help_text="Code or access token returned from the FE interaction with the third party login provider.",
    )
    sign_up_type = serializers.ChoiceField(
        required=False,
        allow_null=True,
        allow_blank=True,
        choices=SignUpType.choices,
        help_text="Provide information about how the user signed up (i.e. via invite or not)",
        write_only=True,
    )
    hubspot_cookie = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    marketing_consent_given = serializers.BooleanField(required=False, allow_null=True)
    utm_data = UTMDataSerializer(required=False, allow_null=True)
    auth_type: AuthType | None = None
    user_model_id_attribute: str = "id"

    class Meta:
        abstract = True

    def create(self, validated_data):  # type: ignore[no-untyped-def]
        user_info = self.get_user_info()  # type: ignore[no-untyped-call]
        if settings.AUTH_CONTROLLER_INSTALLED:
            from auth_controller.controller import (  # type: ignore[import-not-found,import-untyped,unused-ignore]
                is_authentication_method_valid,
            )

            is_authentication_method_valid(
                self.context.get("request"),
                email=user_info.get("email"),
                raise_exception=True,
            )

        user = self._get_user(user_info)
        user_logged_in.send(
            sender=UserModel, request=self.context.get("request"), user=user
        )
        return Token.objects.get_or_create(user=user)[0]

    def _get_user(self, user_data: dict):  # type: ignore[type-arg,no-untyped-def]
        email: str = user_data.pop("email")

        # There are a number of scenarios that we're catering for in this
        # query:
        #  1. A new user arriving, and immediately authenticating with
        #     the given social auth method.
        #  2. A user that has previously authenticated with method A is now
        #     authenticating with method B. Using the `email__iexact` means
        #     that we'll always retrieve the user that already authenticated
        #     with A.
        #  3. A user that (prior to the case sensitivity fix) authenticated
        #     with multiple methods and ended up with duplicate user accounts.
        #     Since it's difficult for us to know which user account they are
        #     using as their primary, we order by the method they are currently
        #     authenticating with and grab the first one in the list.
        existing_user = (
            UserModel.objects.filter(email__iexact=email)
            .order_by(
                F(self.user_model_id_attribute).desc(nulls_last=True),
            )
            .first()
        )

        if not existing_user:
            sign_up_type = self.validated_data.get("sign_up_type")
            self._validate_registration_invite(
                email=email, sign_up_type=self.validated_data.get("sign_up_type")
            )

            user = FFAdminUser.objects.create(
                **user_data, email=email.lower(), sign_up_type=sign_up_type
            )

            # On first OAuth signup, we register the hubspot cookies and utms before creating the hubspot contact
            if request := self.context["request"]:
                register_hubspot_tracker_and_track_user(request, user)

            return user

        elif existing_user.auth_type != self.get_auth_type().value:
            # In this scenario, we're seeing a user that had previously
            # authenticated with another authentication method and is now
            # authenticating with a new OAuth provider.
            setattr(
                existing_user,
                self.user_model_id_attribute,
                user_data[self.user_model_id_attribute],
            )
            existing_user.save()

        return existing_user

    @abstractmethod
    def get_user_info(self):  # type: ignore[no-untyped-def]
        raise NotImplementedError("`get_user_info()` must be implemented.")

    def get_auth_type(self) -> AuthType:
        if not self.auth_type:  # pragma: no cover
            raise NotImplementedError(
                "`auth_type` must be set, or `get_auth_type()` must be implemented."
            )
        return self.auth_type


class GoogleLoginSerializer(OAuthLoginSerializer):
    auth_type = AuthType.GOOGLE
    user_model_id_attribute = "google_user_id"

    def get_user_info(self):  # type: ignore[no-untyped-def]
        return get_user_info(self.validated_data["access_token"])  # type: ignore[no-untyped-call]


class GithubLoginSerializer(OAuthLoginSerializer):
    auth_type = AuthType.GITHUB
    user_model_id_attribute = "github_user_id"

    def get_user_info(self):  # type: ignore[no-untyped-def]
        github_user = GithubUser(code=self.validated_data["access_token"])
        return github_user.get_user_info()
