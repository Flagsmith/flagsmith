from django.http import HttpRequest
from flag_engine.django_transform.document_builders import (
    build_environment_document,
)
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
        environment = Environment.objects.select_related(
            "project", "project__organisation"
        ).get(api_key=request.environment.api_key)
        return Response(build_environment_document(environment))
