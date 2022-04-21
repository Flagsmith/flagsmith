from django.http import HttpRequest
from flag_engine.api.document_builders import build_environment_document
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from environments.authentication import EnvironmentKeyAuthentication
from environments.models import Environment
from environments.permissions.permissions import EnvironmentKeyPermissions


class SDKEnvironmentAPIView(APIView):
    permission_classes = (EnvironmentKeyPermissions,)

    def get_authenticators(self):
        return [EnvironmentKeyAuthentication(required_key_prefix="ser.")]

    def get(self, request: HttpRequest) -> Response:
        try:
            environment = Environment.objects.filter_for_document_builder(
                api_key=request.environment.api_key
            ).get()
        except Environment.DoesNotExist:
            raise NotFound("Environment does not exist for given key.")

        return Response(build_environment_document(environment))
