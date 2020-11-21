from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from custom_auth.oauth.github import GithubUser
from custom_auth.oauth.google import get_user_info

GOOGLE_URL = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&"
UserModel = get_user_model()


class OAuthLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(
        required=True,
        help_text="Code or access token returned from the FE interaction with the third party login provider.",
    )

    class Meta:
        abstract = True

    def create(self, validated_data):
        user_data = self.get_user_info()
        email = user_data.pop("email")
        user, _ = UserModel.objects.get_or_create(email=email, defaults=user_data)
        return Token.objects.get_or_create(user=user)[0]

    def get_user_info(self):
        raise NotImplementedError("`get_user_info()` must be implemented.")


class GoogleLoginSerializer(OAuthLoginSerializer):
    def get_user_info(self):
        return get_user_info(self.validated_data["access_token"])


class GithubLoginSerializer(OAuthLoginSerializer):
    def get_user_info(self):
        github_user = GithubUser(code=self.validated_data["access_token"])
        return github_user.get_user_info()
