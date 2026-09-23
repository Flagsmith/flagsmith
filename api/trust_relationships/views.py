from django.db.models import QuerySet
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import viewsets
from rest_framework.authentication import BaseAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from api_keys.views import ExcludeMasterAPIKeyAuthenticationMixin
from organisations.permissions.permissions import (
    NestedIsOrganisationAdminPermission,
)
from trust_relationships.models import TrustRelationship
from trust_relationships.serializers import (
    TokenExchangeRequestSerializer,
    TokenExchangeResponseSerializer,
    TrustRelationshipSerializer,
)
from trust_relationships.services import (
    delete_trust_relationship,
    exchange_oidc_token,
)


class TrustRelationshipViewSet(
    ExcludeMasterAPIKeyAuthenticationMixin,
    viewsets.ModelViewSet[TrustRelationship],
):
    serializer_class = TrustRelationshipSerializer

    permission_classes = [IsAuthenticated, NestedIsOrganisationAdminPermission]

    def get_queryset(self) -> QuerySet[TrustRelationship]:
        if getattr(self, "swagger_fake_view", False):
            empty: QuerySet[TrustRelationship] = TrustRelationship.objects.none()
            return empty
        queryset: QuerySet[TrustRelationship] = TrustRelationship.objects.filter(
            organisation_id=self.kwargs["organisation_pk"]
        ).select_related("master_api_key")
        return queryset

    def perform_create(self, serializer: BaseSerializer[TrustRelationship]) -> None:
        serializer.save(
            organisation_id=int(self.kwargs["organisation_pk"]),
            created_by=self.request.user,
        )

    def perform_destroy(self, instance: TrustRelationship) -> None:
        delete_trust_relationship(trust_relationship=instance)


class OIDCTokenExchangeView(APIView):
    """Exchange an external OIDC token for a short-lived access token."""

    authentication_classes: list[type[BaseAuthentication]] = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "oidc_token_exchange"

    @extend_schema(
        operation_id="oidc_token_exchange",
        description=(
            "Exchange an OIDC token issued by a trusted identity provider "
            "for a short-lived Flagsmith access token."
        ),
        request=TokenExchangeRequestSerializer,
        responses={
            200: TokenExchangeResponseSerializer,
            400: OpenApiResponse(
                description="Request body is invalid.",
            ),
            401: OpenApiResponse(
                description=(
                    "Token validation failed, or no trust relationship "
                    "matches the token."
                ),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        serializer = TokenExchangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = exchange_oidc_token(serializer.validated_data["token"])
        response_serializer = TokenExchangeResponseSerializer(
            {
                "access_token": result.access_token,
                "token_type": "Bearer",
                "expires_in": result.expires_in,
            }
        )
        return Response(response_serializer.data)
