from rest_framework.permissions import BasePermission

from environments.models import Environment
from organisations.models import Organisation


class TriggerSampleWebhookPermission(BasePermission):
    def has_permission(self, request, view):
        if view.basename == "organisation-webhooks":
            organisation_pk = view.kwargs.get("organisation_pk")
            return is_organisation_admin(organisation_pk, request)
        environment_api_key = view.kwargs.get("environment_api_key")
        return is_environment_admin(environment_api_key, request)


def is_organisation_admin(organisation_pk, request):
    return organisation_pk and request.user.is_admin(
        Organisation.objects.get(pk=organisation_pk)
    )


def is_environment_admin(environment_api_key, request):
    return environment_api_key and request.user.is_environment_admin(
        Environment.objects.get(api_key=environment_api_key)
    )
