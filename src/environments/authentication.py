from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from environments.models import Environment


class EnvironmentKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to add the environment to the request for endpoints used by the clients.
    """

    def authenticate(self, request):
        try:
            request.environment = Environment.objects.get(api_key=request.META.get('HTTP_X_ENVIRONMENT_KEY'))
        except Environment.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or missing Environment Key')
