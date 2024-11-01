from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from organisations.subscriptions.licensing.helpers import verify_signature
from organisations.subscriptions.licensing.models import OrganisationLicence


@api_view(http_method_names=["PUT"])
def create_or_update_licence(
    request: Request, organisation_id: int, **kwargs
) -> Response:
    if "licence" not in request.FILES:
        raise serializers.ValidationError("No licence file provided.")

    if "licence_signature" not in request.FILES:
        raise serializers.ValidationError("No licence signature file provided.")

    licence = request.FILES["licence"].read().decode("utf-8")
    licence_signature = request.FILES["licence_signature"].read().decode("utf-8")

    if verify_signature(licence, licence_signature):
        OrganisationLicence.objects.update_or_create(
            organisation_id=organisation_id,
            defaults={"content": licence},
        )
    else:
        raise serializers.ValidationError("Signature failed for licence.")
    return Response(200)
