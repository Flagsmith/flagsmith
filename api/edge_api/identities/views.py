import base64
import json
import typing

import pydantic
from common.environments.permissions import (  # type: ignore[import-untyped]
    MANAGE_IDENTITIES,
    VIEW_IDENTITIES,
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema  # type: ignore[import-untyped]
from flag_engine.identities.models import IdentityFeaturesList, IdentityModel
from flag_engine.identities.traits.models import TraitModel
from pyngo import drf_error_details
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from app.pagination import (
    EdgeIdentityPagination,
    EdgeIdentityPaginationInspector,
)
from edge_api.identities.serializers import (
    EdgeIdentityFeatureStateSerializer,
    EdgeIdentityFsQueryparamSerializer,
    EdgeIdentityIdentifierSerializer,
    EdgeIdentitySerializer,
    EdgeIdentitySourceIdentityRequestSerializer,
    EdgeIdentityTraitsSerializer,
    EdgeIdentityUpdateSerializer,
    EdgeIdentityWithIdentifierFeatureStateDeleteRequestBody,
    EdgeIdentityWithIdentifierFeatureStateRequestBody,
    GetEdgeIdentityOverridesQuerySerializer,
    GetEdgeIdentityOverridesSerializer,
    ListEdgeIdentitiesQuerySerializer,
)
from environments.identities.serializers import (
    IdentityAllFeatureStatesSerializer,
)
from environments.models import Environment
from environments.permissions.permissions import NestedEnvironmentPermissions
from features.models import FeatureState
from features.permissions import IdentityFeatureStatePermissions
from projects.exceptions import DynamoNotEnabledError

from . import edge_identity_service
from .exceptions import TraitPersistenceError
from .models import EdgeIdentity
from .permissions import (
    EdgeIdentityWithIdentifierViewPermissions,
    GetEdgeIdentityOverridesPermission,
)
from .search import EdgeIdentitySearchData


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        pagination_class=EdgeIdentityPagination,
        paginator_inspectors=[EdgeIdentityPaginationInspector],
    ),
)
class EdgeIdentityViewSet(
    GenericViewSet,  # type: ignore[type-arg]
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    UpdateModelMixin,
):
    pagination_class = EdgeIdentityPagination
    lookup_field = "identity_uuid"

    def initial(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        environment = self.get_environment_from_request()
        if not environment.project.enable_dynamo_db:
            raise DynamoNotEnabledError()

        super().initial(request, *args, **kwargs)

    def get_serializer_class(self):  # type: ignore[no-untyped-def]
        if self.action in ("update", "partial_update"):
            return EdgeIdentityUpdateSerializer
        return EdgeIdentitySerializer

    def get_object(self) -> EdgeIdentity:
        identity_document = EdgeIdentity.dynamo_wrapper.get_item_from_uuid_or_404(
            self.kwargs["identity_uuid"]
        )
        edge_identity = EdgeIdentity.from_identity_document(identity_document)
        self.check_object_permissions(self.request, edge_identity)
        return edge_identity

    def get_queryset(self):  # type: ignore[no-untyped-def]
        page_size = self.pagination_class().get_page_size(self.request)

        query_serializer = ListEdgeIdentitiesQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)

        start_key = None
        if previous_last_evaluated_key := query_serializer.validated_data.get(
            "last_evaluated_key"
        ):
            start_key = json.loads(base64.b64decode(previous_last_evaluated_key))

        search_query: typing.Optional[EdgeIdentitySearchData]
        if not (search_query := query_serializer.validated_data.get("q")):
            return EdgeIdentity.dynamo_wrapper.get_all_items(
                self.kwargs["environment_api_key"],
                page_size,  # type: ignore[arg-type]
                start_key,
            )

        return EdgeIdentity.dynamo_wrapper.search_items(
            environment_api_key=self.kwargs["environment_api_key"],
            search_data=search_query,
            limit=page_size,  # type: ignore[arg-type]
            start_key=start_key,  # type: ignore[arg-type]
        )

    def get_permissions(self) -> list[BasePermission]:
        return [
            IsAuthenticated(),
            NestedEnvironmentPermissions(
                action_permission_map={
                    "retrieve": VIEW_IDENTITIES,
                    "list": VIEW_IDENTITIES,
                    "create": MANAGE_IDENTITIES,
                    "destroy": MANAGE_IDENTITIES,
                    "get_traits": VIEW_IDENTITIES,
                    "update_traits": MANAGE_IDENTITIES,
                },
            ),
        ]

    def get_environment_from_request(self) -> Environment:
        """
        Get environment object from URL parameters in request.
        """
        return get_object_or_404(
            Environment, api_key=self.kwargs["environment_api_key"]
        )

    def perform_destroy(self, instance: EdgeIdentity) -> None:
        instance.delete(user=self.request.user)  # type: ignore[arg-type]

    @swagger_auto_schema(
        responses={200: EdgeIdentityTraitsSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="list-traits")
    def get_traits(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        edge_identity = self.get_object()
        data = [
            trait.dict()
            for trait in edge_identity.engine_identity_model.identity_traits
        ]
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method="put",
        request_body=EdgeIdentityTraitsSerializer,
        responses={200: EdgeIdentityTraitsSerializer()},
    )
    @action(detail=True, methods=["put"], url_path="update-traits")
    def update_traits(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        environment = self.get_environment_from_request()
        if not environment.project.organisation.persist_trait_data:
            raise TraitPersistenceError()
        edge_identity = self.get_object()
        try:
            trait = TraitModel(**request.data)
        except pydantic.ValidationError as validation_error:
            raise ValidationError(
                drf_error_details(validation_error)
            ) from validation_error
        _, traits_updated = edge_identity.engine_identity_model.update_traits([trait])
        if traits_updated:
            edge_identity.save()

        data = trait.dict()
        return Response(data, status=status.HTTP_200_OK)


class EdgeIdentityFeatureStateViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = [IsAuthenticated, IdentityFeatureStatePermissions]
    lookup_field = "featurestate_uuid"

    serializer_class = EdgeIdentityFeatureStateSerializer
    # Patch is not supported
    http_method_names = [
        "get",
        "post",
        "put",
        "delete",
        "head",
        "options",
        "trace",
    ]
    pagination_class = None

    def get_identity(self, edge_identity_identity_uuid: str) -> EdgeIdentity:
        identity_document = EdgeIdentity.dynamo_wrapper.get_item_from_uuid_or_404(
            edge_identity_identity_uuid
        )

        if (
            identity_document["environment_api_key"]
            != self.kwargs["environment_api_key"]
        ):
            raise PermissionDenied("Identity does not belong to this environment.")
        identity = EdgeIdentity.from_identity_document(identity_document)

        valid_feature_names = set(
            FeatureState.objects.filter(
                environment__api_key=identity.environment_api_key
            ).values_list("feature__name", flat=True)
        )
        identity.synchronise_features(valid_feature_names=valid_feature_names)

        return identity

    def initial(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().initial(request, *args, **kwargs)
        self.identity: EdgeIdentity = self.get_identity(
            edge_identity_identity_uuid=self.kwargs["edge_identity_identity_uuid"]
        )

    def get_object(self):  # type: ignore[no-untyped-def]
        feature_state = self.identity.get_feature_state_by_featurestate_uuid(
            self.kwargs["featurestate_uuid"]
        )
        if not feature_state:
            raise NotFound()

        return feature_state

    def get_serializer_context(self) -> dict:  # type: ignore[type-arg]
        return {
            **super().get_serializer_context(),
            "identity": self.identity,
            "environment": Environment.objects.get(
                api_key=self.kwargs["environment_api_key"]
            ),
        }

    @swagger_auto_schema(query_serializer=EdgeIdentityFsQueryparamSerializer())
    def list(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        q_params_serializer = EdgeIdentityFsQueryparamSerializer(
            data=self.request.query_params
        )
        q_params_serializer.is_valid(raise_exception=True)

        identity_features: IdentityFeaturesList = self.identity.feature_overrides

        feature = q_params_serializer.data.get("feature")
        if feature:
            identity_features = filter(  # type: ignore[assignment]
                lambda fs: fs.feature.id == feature, identity_features
            )

        serializer = self.get_serializer(identity_features, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):  # type: ignore[no-untyped-def]
        self.identity.remove_feature_override(instance)
        self.identity.save(user=self.request.user)  # type: ignore[arg-type]

    @swagger_auto_schema(responses={200: IdentityAllFeatureStatesSerializer(many=True)})
    @action(detail=False, methods=["GET"])
    def all(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        (
            feature_states,
            identity_feature_names,
        ) = self.identity.get_all_feature_states()

        serializer = IdentityAllFeatureStatesSerializer(
            instance=feature_states,
            many=True,
            context={
                "request": request,
                "identity": self.identity,
                "environment_api_key": self.identity.environment_api_key,
                "identity_feature_names": identity_feature_names,
            },
        )

        return Response(serializer.data)

    @swagger_auto_schema(  # type: ignore[misc]
        request_body=EdgeIdentitySourceIdentityRequestSerializer(),
        responses={200: IdentityAllFeatureStatesSerializer(many=True)},
    )
    @action(detail=False, methods=["POST"], url_path="clone-from-given-identity")
    def clone_from_given_identity(self, request, *args, **kwargs) -> Response:  # type: ignore[no-untyped-def]
        """
        Clone feature states from a given source identity.
        """
        # Get and validate source identity
        serializer = EdgeIdentitySourceIdentityRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        source_identity: EdgeIdentity = self.get_identity(
            edge_identity_identity_uuid=serializer.validated_data[
                "source_identity_uuid"
            ]
        )

        self.identity.clone_flag_states_from(source_identity)
        self.identity.save(user=request.user)

        return self.all(request, *args, **kwargs)  # type: ignore[no-any-return]


class EdgeIdentityWithIdentifierFeatureStateView(APIView):
    permission_classes = [IsAuthenticated, EdgeIdentityWithIdentifierViewPermissions]
    pagination_class = None

    def initial(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        super().initial(request, *args, **kwargs)

        serializer = EdgeIdentityIdentifierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = serializer.data["identifier"]
        environment_api_key = self.kwargs["environment_api_key"]

        identity_document = EdgeIdentity.dynamo_wrapper.get_item(
            f"{environment_api_key}_{identifier}"
        )

        if identity_document:
            self.identity = EdgeIdentity.from_identity_document(identity_document)
        else:
            self.identity = EdgeIdentity(
                engine_identity_model=IdentityModel(
                    identifier=identifier, environment_api_key=environment_api_key
                )
            )

    @swagger_auto_schema(
        request_body=EdgeIdentityWithIdentifierFeatureStateRequestBody,
        responses={200: EdgeIdentityFeatureStateSerializer()},
    )
    def put(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        feature = request.data.get("feature")
        feature_state = self.identity.get_feature_state_by_feature_name_or_id(feature)
        serializer = EdgeIdentityFeatureStateSerializer(
            instance=feature_state,
            data=request.data,
            context={
                "view": self,
                "request": request,
                "identity": self.identity,
                "environment": Environment.objects.get(
                    api_key=self.kwargs["environment_api_key"]
                ),
            },
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()  # type: ignore[no-untyped-call]

        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        request_body=EdgeIdentityWithIdentifierFeatureStateDeleteRequestBody,
    )
    def delete(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        feature = request.data.get("feature")
        feature_state = self.identity.get_feature_state_by_feature_name_or_id(feature)
        if feature_state:
            self.identity.remove_feature_override(feature_state)
            self.identity.save(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(  # type: ignore[misc]
    method="GET",
    query_serializer=GetEdgeIdentityOverridesQuerySerializer(),
    responses={200: GetEdgeIdentityOverridesSerializer()},
)
@api_view(http_method_names=["GET"])  # type: ignore[arg-type]
@permission_classes([IsAuthenticated, GetEdgeIdentityOverridesPermission])
def get_edge_identity_overrides(  # type: ignore[no-untyped-def]
    request: Request, environment_api_key: str, **kwargs
) -> Response:
    query_serializer = GetEdgeIdentityOverridesQuerySerializer(
        data=request.query_params
    )
    query_serializer.is_valid(raise_exception=True)
    feature_id = query_serializer.validated_data.get("feature")
    environment = Environment.objects.get(api_key=environment_api_key)
    items = edge_identity_service.get_edge_identity_overrides(
        environment_id=environment.id, feature_id=feature_id
    )
    response_serializer = GetEdgeIdentityOverridesSerializer(
        instance={"results": items}, context={"environment": environment}
    )
    return Response(response_serializer.data)
