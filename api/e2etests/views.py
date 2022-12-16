import os

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from organisations.models import Subscription
from users.models import FFAdminUser

from .permissions import E2ETestPermission


class Teardown(APIView):
    schema = None
    permission_classes = (E2ETestPermission,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        # delete users created for e2e test by front end
        if os.environ["FE_E2E_TEST_USER_EMAIL"]:
            FFAdminUser.objects.filter(
                email=os.environ["FE_E2E_TEST_USER_EMAIL"]
            ).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UpdateSeats(APIView):
    permission_classes = (E2ETestPermission,)
    authentication_classes = (TokenAuthentication,)

    def put(self, request):
        user = FFAdminUser.objects.get(email=os.environ["FE_E2E_TEST_USER_EMAIL"])
        Subscription.objects.filter(organisation__in=user.organisations.all()).update(
            max_seats=request.data.get("seats", 3)
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
