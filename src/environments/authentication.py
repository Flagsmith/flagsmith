from django.core.cache import cache
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from environments.models import Environment


class EnvironmentKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to add the environment to the request for endpoints used by the clients.
    """
    def authenticate(self, request):
        try:
            environment = cache.get(request.META.get('HTTP_X_ENVIRONMENT_KEY'))
            if not environment:
                environment = Environment.objects.select_related('project', 'project__organisation').get(
                    api_key=request.META.get('HTTP_X_ENVIRONMENT_KEY'))
                cache.set(environment.api_key, environment)
        except Environment.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid or missing Environment Key')

        if not self._can_serve_flags(environment):
            raise exceptions.AuthenticationFailed('Organisation is disabled from serving flags.')

        request.environment = environment

    def _can_serve_flags(self, environment):
        return not environment.project.organisation.stop_serving_flags
