import coreapi
from django.db.models import Q
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from environments.authentication import EnvironmentKeyAuthentication
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import (
    IncrementTraitValueSerializer,
    TraitSerializerBasic,
    TraitSerializerFull,
)
from environments.models import Environment
from environments.permissions.permissions import (
    EnvironmentKeyPermissions,
    TraitPersistencePermissions,
)
from environments.sdk.serializers import (
    SDKBulkCreateUpdateTraitSerializer,
    SDKCreateUpdateTraitSerializer,
)
from environments.views import logger
from util.views import SDKAPIView


class TraitViewSet(viewsets.ModelViewSet):
    serializer_class = TraitSerializerFull

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        environment_api_key = self.kwargs["environment_api_key"]

        identity_identifier = self.kwargs.get("identity_identifier")
        environment = self.request.user.get_permitted_environments(
            ["VIEW_ENVIRONMENT"]
        ).get(api_key=environment_api_key)

        if identity_identifier:
            identity = Identity.objects.get(
                identifier=identity_identifier, environment=environment
            )
        else:
            identity = None

        return Trait.objects.filter(identity=identity)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        return Environment.objects.get(api_key=self.kwargs["environment_api_key"])

    def create(self, request, *args, **kwargs):
        """
        Override create method to add identity (if present) from URL parameters.

        TODO: fix this - it doesn't work, the FE uses the SDK endpoint instead
        """
        data = request.data
        environment = self.get_environment_from_request()
        if (
            environment.project.organisation
            not in self.request.user.organisations.all()
        ):
            return Response(status=status.HTTP_403_FORBIDDEN)

        identity_pk = self.kwargs.get("identity_pk")

        # check if identity in data or in request
        if "identity" not in data and not identity_pk:
            error = {"detail": "Identity not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # TODO: do we give priority to request identity or data?
        # Override with request identity
        if identity_pk:
            data["identity"] = identity_pk

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def update(self, request, *args, **kwargs):
        """
        Override update method to always assume update request is partial and create / update
        trait value.
        """
        trait_to_update = self.get_object()
        trait_data = request.data

        # Check if trait value was provided with request data. If so, we need to figure out value_type from
        # the given value and also use correct value field e.g. boolean_value, float_value, integer_value or
        # string_value, and override request data
        if "trait_value" in trait_data:
            trait_data = trait_to_update.generate_trait_value_data(
                trait_data["trait_value"]
            )

        serializer = TraitSerializerFull(trait_to_update, data=trait_data, partial=True)

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update as overridden update method assumes partial True for all requests.
        """
        return self.update(request, *args, **kwargs)

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
        delete_all_traits = request.query_params.get("deleteAllMatchingTraits")
        if delete_all_traits and delete_all_traits in ("true", "True"):
            trait = self.get_object()
            self._delete_all_traits_matching_key(
                trait.trait_key, trait.identity.environment
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return super(TraitViewSet, self).destroy(request, *args, **kwargs)

    def _delete_all_traits_matching_key(self, trait_key, environment):
        Trait.objects.filter(
            trait_key=trait_key, identity__environment=environment
        ).delete()


class SDKTraitsDeprecated(SDKAPIView):
    # API to handle /api/v1/identities/<identifier>/traits/<trait_key> endpoints
    # if Identity or Trait does not exist it will create one, otherwise will fetch existing
    serializer_class = TraitSerializerBasic

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(
                "X-Environment-Key",
                location="header",
                description="API Key for an Environment",
            ),
            coreapi.Field(
                "identifier",
                location="path",
                required=True,
                description="Identity user identifier",
            ),
            coreapi.Field(
                "trait_key",
                location="path",
                required=True,
                description="User trait unique key",
            ),
        ]
    )

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
        return Response(serializer.data, status=200)

    @swagger_auto_schema(request_body=SDKCreateUpdateTraitSerializer(many=True))
    @action(detail=False, methods=["PUT"], url_path="bulk")
    def bulk_create(self, request):
        try:
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
            return Response(serializer.data, status=200)

        except (TypeError, AttributeError) as excinfo:
            logger.error("Invalid request data: %s" % str(excinfo))
            return Response(
                {"detail": "Invalid request data"}, status=status.HTTP_400_BAD_REQUEST
            )
