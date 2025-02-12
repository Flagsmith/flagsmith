from common.environments.permissions import MANAGE_IDENTITIES, VIEW_IDENTITIES
from django.conf import settings
from django.core.exceptions import BadRequest
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edge_api.identities.edge_request_forwarder import (
    forward_trait_request,
    forward_trait_requests,
)
from environments.authentication import EnvironmentKeyAuthentication
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import (
    IncrementTraitValueSerializer,
    TraitSerializer,
    TraitSerializerBasic,
    TraitSerializerFull,
)
from environments.permissions.permissions import (
    EnvironmentKeyPermissions,
    NestedEnvironmentPermissions,
    TraitPersistencePermissions,
)
from environments.sdk.serializers import (
    SDKBulkCreateUpdateTraitSerializer,
    SDKCreateUpdateTraitSerializer,
)
from environments.views import logger
from util.views import SDKAPIView


class TraitViewSet(viewsets.ModelViewSet):
    serializer_class = TraitSerializer

    def initial(self, request, *args, **kwargs):
        # Add environment and identity to request(used by generate_identity_update_message decorator)
        identity = Identity.objects.select_related("environment").get(
            pk=self.kwargs["identity_pk"]
        )
        if not identity.environment.api_key == self.kwargs["environment_api_key"]:
            raise Identity.DoesNotExist()

        request.identity = identity
        request.environment = identity.environment

        self.identity = identity

        super().initial(request, *args, **kwargs)

    def get_queryset(self):
        """
        Override queryset to filter based on the parent identity.
        """
        if getattr(self, "swagger_fake_view", False):
            return Trait.objects.none()

        return Trait.objects.filter(identity=self.identity)

    def get_permissions(self):
        return [
            IsAuthenticated(),
            NestedEnvironmentPermissions(
                action_permission_map={
                    "create": MANAGE_IDENTITIES,
                    "update": MANAGE_IDENTITIES,
                    "partial_update": MANAGE_IDENTITIES,
                    "destroy": MANAGE_IDENTITIES,
                    "list": VIEW_IDENTITIES,
                    "retrieve": VIEW_IDENTITIES,
                },
                get_environment_from_object_callable=lambda t: t.identity.environment,
            ),
        ]

    def perform_create(self, serializer):
        serializer.save(identity=self.identity)

    def perform_update(self, serializer):
        serializer.save(identity=self.identity)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "deleteAllMatchingTraits",
                openapi.IN_QUERY,
                "Deletes all traits in this environment matching the key of the deleted trait",
                type=openapi.TYPE_BOOLEAN,
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        if request.query_params.get("deleteAllMatchingTraits") in ("true", "True"):
            trait = self.get_object()
            Trait.objects.filter(
                trait_key=trait.trait_key,
                identity__environment=trait.identity.environment,
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return super(TraitViewSet, self).destroy(request, *args, **kwargs)


class SDKTraitsDeprecated(SDKAPIView):
    # API to handle /api/v1/identities/<identifier>/traits/<trait_key> endpoints
    # if Identity or Trait does not exist it will create one, otherwise will fetch existing
    serializer_class = TraitSerializerBasic
    throttle_classes = []

    schema = None

    def post(self, request, identifier, trait_key, *args, **kwargs):
        """
        THIS ENDPOINT IS DEPRECATED. Please use `/traits/` instead.
        """
        trait_data = request.data

        if "trait_value" not in trait_data:
            error = {"detail": "Trait value not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # if we have identifier fetch, or create if does not exist
        if identifier:
            identity, _ = Identity.objects.get_or_create(
                identifier=identifier,
                environment=request.environment,
            )

        else:
            return Response(
                {"detail": "Missing identifier"}, status=status.HTTP_400_BAD_REQUEST
            )

        # if we have identity trait fetch, or create if does not exist
        if trait_key:
            # need to create one if does not exist
            trait, _ = Trait.objects.get_or_create(
                identity=identity,
                trait_key=trait_key,
            )

        else:
            return Response(
                {"detail": "Missing trait key"}, status=status.HTTP_400_BAD_REQUEST
            )

        if trait and "trait_value" in trait_data:
            # Check if trait value was provided with request data. If so, we need to figure out value_type from
            # the given value and also use correct value field e.g. boolean_value, float_value, integer_value or
            # string_value, and override request data
            trait_data = trait.generate_trait_value_data(trait_data["trait_value"])

            trait_full_serializer = TraitSerializerFull(
                trait, data=trait_data, partial=True
            )

            if trait_full_serializer.is_valid():
                trait_full_serializer.save()
                return Response(
                    self.get_serializer(trait).data, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    trait_full_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response(
                {"detail": "Failed to update user trait"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SDKTraits(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = (EnvironmentKeyPermissions, TraitPersistencePermissions)
    authentication_classes = (EnvironmentKeyAuthentication,)
    throttle_classes = []

    def get_serializer_class(self):
        if self.action == "increment_value":
            return IncrementTraitValueSerializer
        if self.action == "bulk_create":
            return SDKBulkCreateUpdateTraitSerializer

        return SDKCreateUpdateTraitSerializer

    def get_serializer_context(self):
        context = super(SDKTraits, self).get_serializer_context()
        context["environment"] = self.request.environment
        return context

    @swagger_auto_schema(request_body=SDKCreateUpdateTraitSerializer)
    def create(self, request, *args, **kwargs):
        response = super(SDKTraits, self).create(request, *args, **kwargs)
        response.status_code = status.HTTP_200_OK
        if settings.EDGE_API_URL and request.environment.project.enable_dynamo_db:
            forward_trait_request.delay(
                args=(
                    request.method,
                    dict(request.headers),
                    request.environment.project.id,
                    request.data,
                )
            )

        return response

    @swagger_auto_schema(
        responses={200: IncrementTraitValueSerializer},
        request_body=IncrementTraitValueSerializer,
    )
    @action(detail=False, methods=["POST"], url_path="increment-value")
    def increment_value(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if settings.EDGE_API_URL and request.environment.project.enable_dynamo_db:
            # Convert the payload to the structure expected by /traits
            payload = serializer.data.copy()
            payload.update({"identity": {"identifier": payload.pop("identifier")}})
            forward_trait_request.delay(
                args=(
                    request.method,
                    dict(request.headers),
                    request.environment.project.id,
                    payload,
                )
            )

        return Response(serializer.data, status=200)

    @swagger_auto_schema(request_body=SDKCreateUpdateTraitSerializer(many=True))
    @action(detail=False, methods=["PUT"], url_path="bulk")
    def bulk_create(self, request):
        try:
            if not request.environment.trait_persistence_allowed(request):
                raise BadRequest("Unable to set traits with client key.")

            # endpoint allows users to delete existing traits by sending null values
            # for the trait value so we need to filter those out here
            traits = []
            delete_filter_query = Q()

            for trait in request.data:
                if trait.get("trait_value") is None:
                    delete_filter_query = delete_filter_query | Q(
                        trait_key=trait.get("trait_key"),
                        identity__identifier=trait["identity"]["identifier"],
                        identity__environment=request.environment,
                    )
                else:
                    traits.append(trait)

            if delete_filter_query:
                Trait.objects.filter(delete_filter_query).delete()

            serializer = self.get_serializer(data=traits, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            if settings.EDGE_API_URL and request.environment.project.enable_dynamo_db:
                forward_trait_requests.delay(
                    args=(
                        request.method,
                        dict(request.headers),
                        request.environment.project.id,
                        request.data,
                    )
                )

            return Response(serializer.data, status=200)

        except (TypeError, AttributeError) as excinfo:
            logger.error("Invalid request data: %s" % str(excinfo))
            return Response(
                {"detail": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST
            )
