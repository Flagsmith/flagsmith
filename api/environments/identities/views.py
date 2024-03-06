import typing
from collections import namedtuple

from core.constants import FLAGSMITH_UPDATED_AT_HEADER
from core.request_origin import RequestOrigin
from django.conf import settings
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.pagination import CustomPagination
from edge_api.identities.edge_request_forwarder import forward_identity_request
from environments.identities.models import Identity
from environments.identities.serializers import (
    IdentitySerializer,
    SDKIdentitiesQuerySerializer,
    SDKIdentitiesResponseSerializer,
)
from environments.models import Environment
from environments.permissions.constants import (
    MANAGE_IDENTITIES,
    VIEW_IDENTITIES,
)
from environments.permissions.permissions import NestedEnvironmentPermissions
from environments.sdk.serializers import (
    IdentifyWithTraitsSerializer,
    IdentitySerializerWithTraitsAndSegments,
)
from features.serializers import SDKFeatureStateSerializer
from integrations.integration import (
    IDENTITY_INTEGRATIONS,
    identify_integrations,
)
from util.views import SDKAPIView


class IdentityViewSet(viewsets.ModelViewSet):
    serializer_class = IdentitySerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Identity.objects.none()

        environment = self.get_environment_from_request()
        queryset = Identity.objects.filter(environment=environment)

        search_query = self.request.query_params.get("q")
        if search_query:
            if search_query.startswith('"') and search_query.endswith('"'):
                # Quoted searches should do an exact match just like Google
                queryset = queryset.filter(
                    identifier__exact=search_query.replace('"', "")
                )
            else:
                # Otherwise do a fuzzy search
                queryset = queryset.filter(identifier__icontains=search_query)

        # change the default order by to avoid performance issues with pagination
        # when environments have small number (<page_size) of records
        queryset = queryset.order_by("created_date")

        return queryset

    def get_permissions(self):
        return [
            IsAuthenticated(),
            NestedEnvironmentPermissions(
                action_permission_map={
                    "list": VIEW_IDENTITIES,
                    "retrieve": VIEW_IDENTITIES,
                    "create": MANAGE_IDENTITIES,
                    "update": MANAGE_IDENTITIES,
                    "partial_update": MANAGE_IDENTITIES,
                    "destroy": MANAGE_IDENTITIES,
                },
            ),
        ]

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        return Environment.objects.get(api_key=self.kwargs["environment_api_key"])

    def perform_create(self, serializer):
        environment = self.get_environment_from_request()
        serializer.save(environment=environment)

    def perform_update(self, serializer):
        environment = self.get_environment_from_request()
        serializer.save(environment=environment)


class SDKIdentitiesDeprecated(SDKAPIView):
    """
    THIS ENDPOINT IS DEPRECATED. Please use `/identities/?identifier=<identifier>` instead.
    """

    # API to handle /api/v1/identities/ endpoint to return Flags and Traits for user Identity
    # if Identity does not exist it will create one, otherwise will fetch existing

    serializer_class = IdentifyWithTraitsSerializer
    throttle_classes = []

    schema = None

    # identifier is in a path parameter
    def get(self, request, identifier, *args, **kwargs):
        # if we have identifier fetch, or create if does not exist
        if identifier:
            identity, _ = Identity.objects.get_or_create_for_sdk(
                identifier=identifier,
                environment=request.environment,
                integrations=IDENTITY_INTEGRATIONS,
            )
        else:
            return Response(
                {"detail": "Missing identifier"}, status=status.HTTP_400_BAD_REQUEST
            )

        if identity:
            traits_data = identity.get_all_user_traits()
            # traits_data = self.get_serializer(identity.get_all_user_traits(), many=True)
            # return Response(traits.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Given identifier not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # We need object type to pass into our IdentitySerializerTraitFlags
        IdentityFlagsWithTraitsAndSegments = namedtuple(
            "IdentityTraitFlagsSegments", ("flags", "traits", "segments")
        )
        identity_flags_traits_segments = IdentityFlagsWithTraitsAndSegments(
            flags=identity.get_all_feature_states(),
            traits=traits_data,
            segments=identity.get_segments(),
        )

        serializer = IdentitySerializerWithTraitsAndSegments(
            identity_flags_traits_segments
        )

        return Response(serializer.data, status=status.HTTP_200_OK)


class SDKIdentities(SDKAPIView):
    serializer_class = IdentifyWithTraitsSerializer
    pagination_class = None  # set here to ensure documentation is correct
    throttle_classes = []

    @swagger_auto_schema(
        responses={200: SDKIdentitiesResponseSerializer()},
        query_serializer=SDKIdentitiesQuerySerializer(),
        operation_id="identify_user",
    )
    @method_decorator(
        cache_page(
            timeout=settings.GET_IDENTITIES_ENDPOINT_CACHE_SECONDS,
            cache=settings.GET_IDENTITIES_ENDPOINT_CACHE_NAME,
        )
    )
    def get(self, request):
        identifier = request.query_params.get("identifier")
        if not identifier:
            return Response(
                {"detail": "Missing identifier"}
            )  # TODO: add 400 status - will this break the clients?

        identity, _ = Identity.objects.get_or_create_for_sdk(
            identifier=identifier,
            environment=request.environment,
            integrations=IDENTITY_INTEGRATIONS,
        )
        self.identity = identity

        if settings.EDGE_API_URL and request.environment.project.enable_dynamo_db:
            forward_identity_request.delay(
                args=(
                    request.method,
                    dict(request.headers),
                    request.environment.project.id,
                ),
                kwargs={"query_params": request.GET.dict()},
            )

        # Note that we send the environment updated_at value here since it covers most use cases
        # in which an identity will need updated flags. It will not cover identity overrides or
        # adding traits to the identity (which adds / removes them to / from segments).
        # TODO: handle identity overrides.
        headers = {
            FLAGSMITH_UPDATED_AT_HEADER: request.environment.updated_at.timestamp()
        }

        feature_name = request.query_params.get("feature")
        if feature_name:
            response = self._get_single_feature_state_response(
                identity, feature_name, headers=headers
            )
        else:
            response = self._get_all_feature_states_for_user_response(
                identity, headers=headers
            )

        return response

    def get_serializer_context(self):
        context = super(SDKIdentities, self).get_serializer_context()
        if hasattr(self.request, "environment"):
            # only set it if the request has the attribute to ensure that the
            # documentation works correctly still
            context["environment"] = self.request.environment
            if getattr(self, "identity", None):
                context["identity"] = self.identity
        context["feature_states_additional_filters"] = self._get_additional_filters()
        return context

    @swagger_auto_schema(
        request_body=IdentifyWithTraitsSerializer(),
        responses={200: SDKIdentitiesResponseSerializer()},
        operation_id="identify_user_with_traits",
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        self.identity = instance.get("identity")

        if settings.EDGE_API_URL and request.environment.project.enable_dynamo_db:
            forward_identity_request.delay(
                args=(
                    request.method,
                    dict(request.headers),
                    request.environment.project.id,
                ),
                kwargs={"request_data": request.data},
            )

        # we need to serialize the response again to ensure that the
        # trait values are serialized correctly
        response_serializer = IdentifyWithTraitsSerializer(
            instance=instance,
            context=self.get_serializer_context(),
        )
        return Response(
            response_serializer.data,
            headers={
                FLAGSMITH_UPDATED_AT_HEADER: request.environment.updated_at.timestamp()
            },
        )

    def _get_additional_filters(self) -> Q | None:
        if self.request.originated_from is RequestOrigin.CLIENT:
            return Q(feature__is_server_key_only=False)
        return None

    def _get_single_feature_state_response(
        self,
        identity: Identity,
        feature_name: str,
        headers: dict[str, typing.Any],
    ) -> Response:
        context = self.get_serializer_context()

        for feature_state in identity.get_all_feature_states(
            additional_filters=self._get_additional_filters(),
        ):
            if feature_state.feature.name == feature_name:
                serializer = SDKFeatureStateSerializer(feature_state, context=context)
                return Response(
                    data=serializer.data, status=status.HTTP_200_OK, headers=headers
                )

        return Response(
            {"detail": "Given feature not found"},
            status=status.HTTP_404_NOT_FOUND,
            headers=headers,
        )

    def _get_all_feature_states_for_user_response(
        self,
        identity: Identity,
        headers: dict[str, typing.Any],
    ):
        """
        Get all feature states for an identity

        :param identity: Identity model to return feature states for
        :return: Response containing lists of both serialized flags and traits
        """
        all_feature_states = identity.get_all_feature_states(
            additional_filters=self._get_additional_filters(),
        )
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            {
                "flags": all_feature_states,
                "traits": identity.identity_traits.all(),
            },
            context=self.get_serializer_context(),
        )

        identify_integrations(identity, all_feature_states)

        return Response(
            data=serializer.data, status=status.HTTP_200_OK, headers=headers
        )
