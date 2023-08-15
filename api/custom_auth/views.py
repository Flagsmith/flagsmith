from django.contrib.auth import user_logged_out
from django.utils.decorators import method_decorator
from djoser.views import UserViewSet
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from trench.views.authtoken import (
    AuthTokenLoginOrRequestMFACode,
    AuthTokenLoginWithMFACode,
)

from custom_auth.serializers import CustomUserDelete
from users.constants import DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE

from .models import UserPasswordResetRequest


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


@method_decorator(
    name="destroy",
    decorator=swagger_auto_schema(query_serializer=CustomUserDelete()),
)
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

    def perform_destroy(self, instance):
        instance.delete(
            delete_orphan_organisations=self.request.data.get(
                "delete_orphan_organisations",
                DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE,
            )
        )

    @action(["post"], detail=False)
    def reset_password(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.get_user()
        if user and user.can_send_password_reset_email():
            super().reset_password(request, *args, **kwargs)
            UserPasswordResetRequest.objects.create(user=user)

        return Response(status=status.HTTP_204_NO_CONTENT)
