from django.contrib.auth import user_logged_out
from django.http import HttpResponseBadRequest
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from trench.views.authtoken import (
    AuthTokenLoginOrRequestMFACode,
    AuthTokenLoginWithMFACode,
)

from users.models import FFAdminUser


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


class ThrottledUserViewSet(UserViewSet):
    throttle_scope = "signup"

    def get_throttles(self):
        """
        Used for throttling create(signup) action
        """
        throttles = []
        if self.action == "create":
            throttles = [ScopedRateThrottle()]
        return throttles


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_token(request):
    Token.objects.filter(user=request.user).delete()
    user_logged_out.send(
        sender=request.user.__class__, request=request, user=request.user
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserDeleteView(UserViewSet):
    def destroy(self, request, *args, **kwargs):
        if "delete_orphan_organizations" in request.query_params:
            delete_orphan_organizations = request.query_params[
                "delete_orphan_organizations"
            ]
            if delete_orphan_organizations.lower() == "true":
                FFAdminUser.delete_orphan_organisations(request.user)
                return Response(status=status.HTTP_204_NO_CONTENT)
            elif delete_orphan_organizations.lower() == "false":
                return super().destroy(request, *args, **kwargs)
            else:
                return HttpResponseBadRequest(
                    "Invalid value for delete_orphan_organizations"
                )
        else:
            return super().destroy(request, *args, **kwargs)
