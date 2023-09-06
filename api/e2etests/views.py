import os

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from .e2e_seed_data import E2ESeedData
from .permissions import E2ETestPermission


class Teardown(APIView):
    schema = None
    permission_classes = (E2ETestPermission,)
    authentication_classes = (TokenAuthentication,)
    e2e_seed_data = E2ESeedData()

    def post(self, request):
        if "ENABLE_FE_E2E" not in os.environ:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self.e2e_seed_data.teardown()
        self.e2e_seed_data.seed_data()
        return Response(status=status.HTTP_204_NO_CONTENT)
