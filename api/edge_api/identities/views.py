import base64
import json
import typing

import marshmallow
from boto3.dynamodb.conditions import Key
from django.db.models import Q
from django.utils.decorators import method_decorator
from drf_yasg2.utils import swagger_auto_schema
from flag_engine.api.schemas import APITraitSchema
from flag_engine.features.models import FeatureStateModel
from flag_engine.identities.builders import (
    build_identity_dict,
    build_identity_model,
)
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.pagination import (
    EdgeIdentityPagination,
    EdgeIdentityPaginationInspector,
)
from edge_api.identities.serializers import (
    EdgeIdentityFeatureStateSerializer,
    EdgeIdentityFsQueryparamSerializer,
    EdgeIdentitySerializer,
    EdgeIdentityTraitsSerializer,
)
from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.constants import MANAGE_IDENTITIES
from environments.permissions.permissions import NestedEnvironmentPermissions
from features.models import FeatureState
from features.permissions import IdentityFeatureStatePermissions
from projects.exceptions import DynamoNotEnabledError

from .exceptions import TraitPersistenceError

trait_schema = APITraitSchema()


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        pagination_class=EdgeIdentityPagination,
        paginator_inspectors=[EdgeIdentityPaginationInspector],
    ),
)
class EdgeIdentityViewSet(viewsets.ModelViewSet):
    serializer_class = EdgeIdentitySerializer
    pagination_class = EdgeIdentityPagination
    lookup_field = "identity_uuid"
    dynamo_identifier_search_functions = {
        "EQUAL": lambda identifier: Key("identifier").eq(identifier),
        "BEGINS_WITH": lambda identifier: Key("identifier").begins_with(identifier),
    }

    def initial(self, request, *args, **kwargs):
        environment = self.get_environment_from_request()
        if not environment.project.enable_dynamo_db:
            raise DynamoNotEnabledError()

        super().initial(request, *args, **kwargs)

    def _get_search_function_and_value(
        self,
        search_query: str,
    ) -> typing.Tuple[typing.Callable, str]:
        if search_query.startswith('"') and search_query.endswith('"'):
            return self.dynamo_identifier_search_functions[
                "EQUAL"
            ], search_query.replace('"', "")
        return self.dynamo_identifier_search_functions["BEGINS_WITH"], search_query

    def get_object(self):
        return Identity.dynamo_wrapper.get_item_from_uuid_or_404(
            self.kwargs["identity_uuid"]
        )

    def get_queryset(self):
        page_size = self.pagination_class().get_page_size(self.request)
        previous_last_evaluated_key = self.request.GET.get("last_evaluated_key")
        search_query = self.request.query_params.get("q")
        start_key = None
        if previous_last_evaluated_key:
            start_key = json.loads(base64.b64decode(previous_last_evaluated_key))

        if not search_query:
            return Identity.dynamo_wrapper.get_all_items(
                self.kwargs["environment_api_key"], page_size, start_key
            )
        search_func, search_identifier = self._get_search_function_and_value(
            search_query
        )
        identity_documents = Identity.dynamo_wrapper.search_items_with_identifier(
            self.kwargs["environment_api_key"],
            search_identifier,
            search_func,
            page_size,
            start_key,
        )
        return identity_documents

    def get_permissions(self):
        return [
            IsAuthenticated(),
            NestedEnvironmentPermissions(
                action_permission_map={
                    "retrieve": MANAGE_IDENTITIES,
                    "get_traits": MANAGE_IDENTITIES,
                    "update_traits": MANAGE_IDENTITIES,
                }
            ),
        ]

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        return Environment.objects.get(api_key=self.kwargs["environment_api_key"])

    def perform_destroy(self, instance):
        Identity.dynamo_wrapper.delete_item(instance["composite_key"])

    @swagger_auto_schema(
        responses={200: EdgeIdentityTraitsSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="list-traits")
    def get_traits(self, request, *args, **kwargs):
        identity = self.get_object()
        data = trait_schema.dump(identity["identity_traits"], many=True)
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        method="put",
        request_body=EdgeIdentityTraitsSerializer,
        responses={200: EdgeIdentityTraitsSerializer()},
    )
    @action(detail=True, methods=["put"], url_path="update-traits")
    def update_traits(self, request, *args, **kwargs):
        environment = self.get_environment_from_request()
        if not environment.project.organisation.persist_trait_data:
            raise TraitPersistenceError()
        identity = build_identity_model(self.get_object())
        try:
            trait = trait_schema.load(request.data)
        except marshmallow.ValidationError as validation_error:
            raise ValidationError(validation_error) from validation_error
        identity.update_traits([trait])
        Identity.dynamo_wrapper.put_item(build_identity_dict(identity))
        data = trait_schema.dump(trait)
        return Response(data, status=status.HTTP_200_OK)


class EdgeIdentityFeatureStateViewSet(viewsets.ModelViewSet):
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

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        identity_document = Identity.dynamo_wrapper.get_item_from_uuid_or_404(
            self.kwargs["edge_identity_identity_uuid"]
        )
        self.identity = build_identity_model(identity_document)

    def get_object(self):
        featurestate_uuid = self.kwargs["featurestate_uuid"]
        try:
            featurestate = next(
                filter(
                    lambda fs: fs.featurestate_uuid == featurestate_uuid,
                    self.identity.identity_features,
                )
            )
        except StopIteration:
            raise NotFound()
        return featurestate

    @swagger_auto_schema(query_serializer=EdgeIdentityFsQueryparamSerializer())
    def list(self, request, *args, **kwargs):
        q_params_serializer = EdgeIdentityFsQueryparamSerializer(
            data=self.request.query_params
        )
        q_params_serializer.is_valid(raise_exception=True)

        identity_features = self.identity.identity_features

        feature = q_params_serializer.data.get("feature")
        if feature:
            identity_features = filter(
                lambda fs: fs.feature.id == feature, identity_features
            )

        serializer = self.get_serializer(identity_features, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        self.identity.identity_features.remove(instance)
        Identity.dynamo_wrapper.put_item(build_identity_dict(self.identity))

    @action(detail=False, methods=["GET"])
    def all(self, request, *args, **kwargs):
        django_environment = Environment.objects.get(
            api_key=kwargs["environment_api_key"]
        )

        segment_ids = Identity.dynamo_wrapper.get_segment_ids(self.identity)

        q = Q(identity__isnull=True) & (
            Q(feature_segment__segment__id__in=segment_ids)
            | Q(feature_segment__isnull=True)
        )
        environment_and_segment_feature_states = (
            django_environment.feature_states.select_related(
                "feature", "feature_segment", "feature_segment__segment"
            ).filter(q)
        )

        feature_states = {}
        for feature_state in environment_and_segment_feature_states:
            if (
                feature_state.feature.name not in feature_states
                or feature_state.feature_segment_id is not None
            ):
                feature_states[feature_state.feature.name] = feature_state

        identity_feature_states = self.identity.identity_features
        identity_feature_names = set()
        for identity_feature_state in identity_feature_states:
            feature_name = identity_feature_state.feature.name
            feature_states[feature_name] = identity_feature_state
            identity_feature_names.add(feature_name)

        serializer = EdgeIdentityAllFeatureStatesSerializer(
            instance=feature_states.values(),
            many=True,
            context={
                "request": request,
                "identity": self.identity,
                "identity_feature_names": identity_feature_names,
            },
        )

        return Response(serializer.data)


class EdgeIdentityAllFeatureStatesFeatureSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    type = serializers.CharField()


class EdgeIdentityAllFeatureStatesSegmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class EdgeIdentityAllFeatureStatesMVFeatureOptionSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField()

    def get_value(self, instance) -> typing.Union[int, bool, str]:
        return instance.value


class EdgeIdentityAllFeatureStatesMVFeatureStateValueSerializer(serializers.Serializer):
    multivariate_feature_option = (
        EdgeIdentityAllFeatureStatesMVFeatureOptionSerializer()
    )
    percentage_allocation = serializers.FloatField()


class EdgeIdentityAllFeatureStatesSerializer(serializers.Serializer):
    feature = EdgeIdentityAllFeatureStatesFeatureSerializer()
    enabled = serializers.BooleanField()
    feature_state_value = serializers.SerializerMethodField()
    overridden_by = serializers.SerializerMethodField()
    segment = serializers.SerializerMethodField()
    multivariate_feature_state_values = (
        EdgeIdentityAllFeatureStatesMVFeatureStateValueSerializer(many=True)
    )

    def get_feature_state_value(
        self, instance: typing.Union[FeatureState, FeatureStateModel]
    ) -> typing.Union[str, int, bool]:
        identity = self.context["identity"]
        identity_id = getattr(identity, "id", None) or getattr(
            identity, "django_id", identity.identity_uuid
        )

        if type(instance) == FeatureState:
            return instance.get_feature_state_value_by_id(identity_id)

        return instance.get_value(identity_id)

    def get_overridden_by(self, instance) -> typing.Optional[str]:
        if getattr(instance, "feature_segment_id", None) is not None:
            return "SEGMENT"
        elif instance.feature.name in self.context.get("identity_feature_names", []):
            return "IDENTITY"
        return None

    def get_segment(
        self, instance
    ) -> typing.Optional[EdgeIdentityAllFeatureStatesSegmentSerializer]:
        if getattr(instance, "feature_segment_id", None) is not None:
            return EdgeIdentityAllFeatureStatesSegmentSerializer(
                instance=instance.feature_segment.segment
            ).data
        return None
