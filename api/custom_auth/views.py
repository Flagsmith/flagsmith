from django.contrib.auth import user_logged_out
from djoser import utils
from djoser.serializers import UserDeleteSerializer
from djoser.views import UserViewSet
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from trench.views.authtoken import (
    AuthTokenLoginOrRequestMFACode,
    AuthTokenLoginWithMFACode,
)


class CustomAuthTokenLoginOrRequestMFACode(AuthTokenLoginOrRequestMFACode):
    """
    Class to handle throttling for login requests
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class CustomAuthTokenLoginWithMFACode(AuthTokenLoginWithMFACode):
    """
    Override class to add throttling
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mfa_code"


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_token(request):
    Token.objects.filter(user=request.user).delete()
    user_logged_out.send(
        sender=request.user.__class__, request=request, user=request.user
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


class UserDeleteQuerySerializer(UserDeleteSerializer):
    delete_orphan_organisations = serializers.BooleanField(default=False)


class FFAdminUserViewSet(UserViewSet):
    throttle_scope = "signup"

    def get_throttles(self):
        """
        Used for throttling create(signup) action
        """
        throttles = []
        if self.action == "create":
            throttles = [ScopedRateThrottle()]
        return throttles

    def get_serializer_class(self):
        if self.action == "destroy" or (
            self.action == "me" and self.request and self.request.method == "DELETE"
        ):
            return UserDeleteQuerySerializer
        else:
            return super().get_serializer_class()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data["delete_orphan_organisations"]:
            instance.delete_orphan_organisations()

        if instance == request.user:
            utils.logout_user(self.request)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
