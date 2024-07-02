from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from organisations.subscriptions.licensing.models import OrganisationLicence


@api_view(http_method_names=["PUT"])
def create_or_update_licence(
    request: Request, organisation_id: int, **kwargs
) -> Response:
    if "licence" not in request.FILES:
        raise serializers.ValidationError("No licence file provided.")

    OrganisationLicence.objects.update_or_create(
        organisation_id=organisation_id,
        defaults={"content": request.FILES["licence"].read().decode("utf-8")},
    )
    return Response(200)
