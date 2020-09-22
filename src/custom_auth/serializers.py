from djoser.serializers import UserCreateSerializer
from rest_framework import serializers
from rest_framework.authtoken.models import Token


class CustomTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ("key",)


class CustomUserCreateSerializer(UserCreateSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # not returning key on registration as need to confirm account first
        # self.fields["key"] = serializers.SerializerMethodField()

    def get_key(self, instance):
        token, _ = Token.objects.get_or_create(user=instance)
        return token.key
