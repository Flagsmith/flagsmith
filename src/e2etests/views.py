import os

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import FFAdminUser


class Teardown(APIView):
    schema = None
    permission_classes = (AllowAny,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        if 'HTTP_X_E2E_TEST_AUTH_TOKEN' not in request.META or \
                'E2E_TEST_AUTH_TOKEN' not in os.environ:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        auth_key = request.META['HTTP_X_E2E_TEST_AUTH_TOKEN']
        allowed_access_key = os.environ['E2E_TEST_AUTH_TOKEN']

        if auth_key != allowed_access_key:
            error = {"detail": "Bad authentication token"}
            return Response(error, status=status.HTTP_401_UNAUTHORIZED)

        # delete users created for e2e test by front end
        if os.environ['FE_E2E_TEST_USER_EMAIL']:
            FFAdminUser.objects.filter(email=os.environ['FE_E2E_TEST_USER_EMAIL']).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
