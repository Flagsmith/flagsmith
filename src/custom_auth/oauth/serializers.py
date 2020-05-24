from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from custom_auth.oauth.google import get_user_info

GOOGLE_URL = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&"
UserModel = get_user_model()


class OAuthAccessTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()

    def create(self, validated_data):
        """
        get or create a user and token based on the access token and return a DRF token

        TODO: make this generic to allow for other oauth access methods
        """
        user_data = get_user_info(validated_data["access_token"])
        email = user_data.pop("email")
        user, _ = UserModel.objects.get_or_create(email=email, defaults=user_data)
        return Token.objects.get_or_create(user=user)[0]
