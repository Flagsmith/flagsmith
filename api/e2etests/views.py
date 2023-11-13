from django.conf import settings
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .e2e_seed_data import seed_data, teardown
from .permissions import E2ETestPermission


class Teardown(APIView):
    schema = None
    permission_classes = (E2ETestPermission,)
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        if not settings.ENABLE_FE_E2E:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        teardown()
        seed_data()
        return Response(status=status.HTTP_204_NO_CONTENT)
