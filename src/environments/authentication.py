from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from environments.models import Environment


class EnvironmentKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to add the environment to the request for endpoints used by the clients.
    """

    def authenticate(self, request):
        try:
            environment = Environment.objects.get(api_key=request.META.get('HTTP_X_ENVIRONMENT_KEY'))
        except Environment.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or missing Environment Key')

        if not self._can_serve_flags(environment):
            raise exceptions.AuthenticationFailed('Organisation is disabled from serving flags.')

        request.environment = environment

    def _can_serve_flags(self, environment):
        return not environment.project.organisation.stop_serving_flags
