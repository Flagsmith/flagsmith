import logging
import typing
from functools import reduce

from app_analytics.analytics_db_service import get_feature_evaluation_data
from app_analytics.influxdb_wrapper import get_multiple_event_list_for_feature
from core.constants import FLAGSMITH_UPDATED_AT_HEADER
from core.request_origin import RequestOrigin
from django.conf import settings
from django.core.cache import caches
from django.db.models import Max, Q, QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from app.pagination import CustomPagination
from environments.authentication import EnvironmentKeyAuthentication
from environments.identities.models import Identity
from environments.identities.serializers import (
    IdentityAllFeatureStatesSerializer,
    IdentitySourceIdentityRequestSerializer,
)
from environments.models import Environment
from environments.permissions.permissions import (
    EnvironmentKeyPermissions,
    NestedEnvironmentPermissions,
)
from features.value_types import BOOLEAN, INTEGER, STRING
from projects.models import Project
from projects.permissions import VIEW_PROJECT
from users.models import FFAdminUser, UserPermissionGroup
from webhooks.webhooks import WebhookEventType

from .constants import INTERSECTION, UNION
from .features_service import get_overrides_data
from .models import Feature, FeatureState
from .permissions import (
    CreateSegmentOverridePermissions,
    EnvironmentFeatureStatePermissions,
    FeaturePermissions,
    FeatureStatePermissions,
    IdentityFeatureStatePermissions,
)
from .serializers import (
    CreateFeatureSerializer,
    CreateSegmentOverrideFeatureStateSerializer,
    FeatureEvaluationDataSerializer,
    FeatureGroupOwnerInputSerializer,
    FeatureInfluxDataSerializer,
    FeatureOwnerInputSerializer,
    FeatureQuerySerializer,
    FeatureStateSerializerBasic,
    FeatureStateSerializerCreate,
    FeatureStateSerializerFull,
    FeatureStateSerializerWithIdentity,
    FeatureStateValueSerializer,
    GetInfluxDataQuerySerializer,
    GetUsageDataQuerySerializer,
    ListFeatureSerializer,
    ProjectFeatureSerializer,
    SDKFeatureStateSerializer,
    SDKFeatureStatesQuerySerializer,
    UpdateFeatureSerializer,
    WritableNestedFeatureStateSerializer,
)
from .tasks import trigger_feature_state_change_webhooks
from .versioning.versioning_service import (
    get_environment_flags_list,
    get_environment_flags_queryset,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

flags_cache = caches[settings.FLAGS_CACHE_LOCATION]


@swagger_auto_schema(responses={200: CreateFeatureSerializer()}, method="get")
@api_view(["GET"])
def get_feature_by_uuid(request, uuid):
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = Feature.objects.filter(project__in=accessible_projects).prefetch_related(
        "multivariate_options", "owners", "tags"
    )
    feature = get_object_or_404(qs, uuid=uuid)
    serializer = CreateFeatureSerializer(instance=feature)
    return Response(serializer.data)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(query_serializer=FeatureQuerySerializer()),
)
class FeatureViewSet(viewsets.ModelViewSet):
    permission_classes = [FeaturePermissions]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        return {
            "list": ListFeatureSerializer,
            "retrieve": ListFeatureSerializer,
            "create": ListFeatureSerializer,
            "update": UpdateFeatureSerializer,
            "partial_update": UpdateFeatureSerializer,
        }.get(self.action, ProjectFeatureSerializer)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Feature.objects.none()

        accessible_projects = self.request.user.get_permitted_projects(VIEW_PROJECT)

        project = get_object_or_404(accessible_projects, pk=self.kwargs["project_pk"])

        queryset = (
            project.features.all()
            .annotate(
                last_modified_in_any_environment=Max(
                    "feature_states__environment_feature_version__created_at",
                    filter=Q(
                        feature_states__environment_feature_version__published_at__isnull=False
                    ),
                ),
            )
            .prefetch_related(
                "multivariate_options", "owners", "tags", "group_owners", "metadata"
            )
        )

        query_serializer = FeatureQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        query_data = query_serializer.validated_data

        queryset = self._filter_queryset(queryset)

        if environment_id := query_data.get("environment"):
            queryset = queryset.annotate(
                last_modified_in_current_environment=Max(
                    "feature_states__environment_feature_version__created_at",
                    filter=Q(
                        feature_states__environment=environment_id,
                        feature_states__environment_feature_version__published_at__isnull=False,
                    ),
                )
            )

        if query_data["value_search"] or query_data["is_enabled"] is not None:
            queryset = self.apply_state_to_queryset(query_data, queryset)
        sort = "%s%s" % (
            "-" if query_data["sort_direction"] == "DESC" else "",
            query_data["sort_field"],
        )
        queryset = queryset.order_by(sort)

        if environment_id:
            page = self.paginate_queryset(queryset)

            self.environment = Environment.objects.get(id=environment_id)
            q = Q(
                feature_id__in=[feature.id for feature in page],
                identity__isnull=True,
                feature_segment__isnull=True,
            )
            feature_states = FeatureState.objects.get_live_feature_states(
                self.environment,
                additional_filters=q,
            ).select_related("feature_state_value", "feature")

            self._feature_states = {fs.feature_id: fs for fs in feature_states}

        return queryset

    def paginate_queryset(self, queryset: QuerySet[Feature]) -> list[Feature]:
        if getattr(self, "_page", None):
            return self._page

        self._page = super().paginate_queryset(queryset)
        return self._page

    def perform_create(self, serializer):
        serializer.save(
            project_id=int(self.kwargs.get("project_pk")), user=self.request.user
        )

    def perform_update(self, serializer):
        serializer.save(project_id=self.kwargs.get("project_pk"))

    def perform_destroy(self, instance):
        feature_states = list(
            instance.feature_states.filter(identity=None, feature_segment=None)
        )
        self._trigger_feature_state_change_webhooks(feature_states)
        instance.delete()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        feature_states = getattr(self, "_feature_states", {})
        project = get_object_or_404(Project.objects.all(), pk=self.kwargs["project_pk"])
        context.update(
            project=project, user=self.request.user, feature_states=feature_states
        )

        if self.action == "list" and "environment" in self.request.query_params:
            environment = get_object_or_404(
                Environment, id=self.request.query_params["environment"]
            )
            context["overrides_data"] = get_overrides_data(environment)

        return context

    def apply_state_to_queryset(
        self, query_data: dict[str, typing.Any], queryset: QuerySet[Feature]
    ) -> QuerySet[Feature]:
        if not query_data.get("environment"):
            raise serializers.ValidationError(
                "Environment is required in order to filter by state search or by state enabled"
            )
        is_enabled = query_data["is_enabled"]
        value_search = query_data["value_search"]
        environment_id = query_data["environment"]

        filter_search_q = Q()
        if value_search is not None:
            filter_search_q = filter_search_q | Q(
                feature_state_value__string_value__icontains=value_search,
                feature_state_value__type=STRING,
            )

            if value_search.lower() in {"true", "false"}:
                boolean_search = value_search.lower() == "true"
                filter_search_q = filter_search_q | Q(
                    feature_state_value__boolean_value=boolean_search,
                    feature_state_value__type=BOOLEAN,
                )

            if value_search.isdigit():
                integer_search = int(value_search)
                filter_search_q = filter_search_q | Q(
                    feature_state_value__integer_value=integer_search,
                    feature_state_value__type=INTEGER,
                )
        filter_enabled_q = Q()
        if is_enabled is not None:
            filter_enabled_q = filter_enabled_q | Q(enabled=is_enabled)

        base_q = Q(
            identity__isnull=True,
            feature_segment__isnull=True,
        )
        if not getattr(self, "environment", None):
            self.environment = Environment.objects.get(id=environment_id)

        feature_states = get_environment_flags_list(
            environment=self.environment,
            additional_filters=base_q,
        )

        feature_ids = FeatureState.objects.filter(
            filter_search_q & filter_enabled_q,
            id__in=[fs.id for fs in feature_states],
        ).values_list("feature_id", flat=True)

        return queryset.filter(id__in=feature_ids)

    @swagger_auto_schema(
        request_body=FeatureGroupOwnerInputSerializer,
        responses={200: ProjectFeatureSerializer},
    )
    @action(detail=True, methods=["POST"], url_path="add-group-owners")
    def add_group_owners(self, request, *args, **kwargs):
        feature = self.get_object()
        data = request.data

        serializer = FeatureGroupOwnerInputSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        if not UserPermissionGroup.objects.filter(
            id__in=serializer.validated_data["group_ids"],
            organisation_id=feature.project.organisation_id,
        ).count() == len(serializer.validated_data["group_ids"]):
            raise serializers.ValidationError("Some groups not found")

        serializer.add_group_owners(feature)
        response = Response(self.get_serializer(instance=feature).data)
        return response

    @swagger_auto_schema(
        request_body=FeatureGroupOwnerInputSerializer,
        responses={200: ProjectFeatureSerializer},
    )
    @action(detail=True, methods=["POST"], url_path="remove-group-owners")
    def remove_group_owners(self, request, *args, **kwargs):
        feature = self.get_object()
        serializer = FeatureGroupOwnerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.remove_group_owners(feature)
        response = Response(self.get_serializer(instance=feature).data)
        return response

    @swagger_auto_schema(
        request_body=FeatureOwnerInputSerializer,
        responses={200: ProjectFeatureSerializer},
    )
    @action(detail=True, methods=["POST"], url_path="add-owners")
    def add_owners(self, request, *args, **kwargs):
        serializer = FeatureOwnerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feature = self.get_object()

        for user in FFAdminUser.objects.filter(
            id__in=serializer.validated_data["user_ids"]
        ):
            if not user.has_project_permission(VIEW_PROJECT, feature.project):
                raise serializers.ValidationError("Some users not found")

        serializer.add_owners(feature)
        return Response(self.get_serializer(instance=feature).data)

    @swagger_auto_schema(
        request_body=FeatureOwnerInputSerializer,
        responses={200: ProjectFeatureSerializer},
    )
    @action(detail=True, methods=["POST"], url_path="remove-owners")
    def remove_owners(self, request, *args, **kwargs):
        serializer = FeatureOwnerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        feature = self.get_object()
        serializer.remove_users(feature)

        return Response(self.get_serializer(instance=feature).data)

    @swagger_auto_schema(
        query_serializer=GetInfluxDataQuerySerializer(),
        responses={200: FeatureInfluxDataSerializer()},
        deprecated=True,
        operation_description="Please use ​/api​/v1​/projects​/{project_pk}​/features​/{id}​/evaluation-data/",
    )
    @action(detail=True, methods=["GET"], url_path="influx-data")
    def get_influx_data(self, request, pk, project_pk):
        feature = get_object_or_404(Feature, pk=pk)

        query_serializer = GetInfluxDataQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        events_list = get_multiple_event_list_for_feature(
            feature_name=feature.name, **query_serializer.data
        )
        serializer = FeatureInfluxDataSerializer(instance={"events_list": events_list})
        return Response(serializer.data)

    @swagger_auto_schema(
        query_serializer=GetUsageDataQuerySerializer(),
        responses={200: FeatureEvaluationDataSerializer()},
    )
    @action(detail=True, methods=["GET"], url_path="evaluation-data")
    def get_evaluation_data(self, request, pk, project_pk):
        feature = get_object_or_404(Feature, pk=pk)

        query_serializer = GetUsageDataQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        usage_data = get_feature_evaluation_data(
            feature=feature, **query_serializer.data
        )
        serializer = FeatureEvaluationDataSerializer(usage_data, many=True)

        return Response(serializer.data)

    def _trigger_feature_state_change_webhooks(
        self, feature_states: typing.List[FeatureState]
    ):
        for feature_state in feature_states:
            trigger_feature_state_change_webhooks(
                feature_state, WebhookEventType.FLAG_DELETED
            )

    def filter_owners_and_group_owners(
        self,
        queryset: QuerySet[Feature],
        query_data: dict[str, typing.Any],
    ) -> QuerySet[Feature]:
        owners_q = Q()
        if query_data.get("owners"):
            owners_q = owners_q | Q(
                owners__id__in=query_data["owners"],
            )

        group_owners_q = Q()
        if query_data.get("group_owners"):
            group_owners_q = group_owners_q | Q(
                group_owners__id__in=query_data["group_owners"],
            )

        return queryset.filter(owners_q | group_owners_q)

    def _filter_queryset(self, queryset: QuerySet[Feature]) -> QuerySet[Feature]:
        query_serializer = FeatureQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        query_data = query_serializer.validated_data

        if query_data.get("search"):
            queryset = queryset.filter(name__icontains=query_data["search"])

        if "tags" in query_serializer.initial_data:
            if query_data.get("tags", "") == "":
                queryset = queryset.filter(tags__isnull=True)
            elif query_data["tag_strategy"] == UNION:
                queryset = queryset.filter(tags__in=query_data["tags"])
            else:
                assert query_data["tag_strategy"] == INTERSECTION
                queryset = reduce(
                    lambda qs, tag_id: qs.filter(tags=tag_id),
                    query_data["tags"],
                    queryset,
                )

        if "is_archived" in query_serializer.initial_data:
            queryset = queryset.filter(is_archived=query_data["is_archived"])

        queryset = self.filter_owners_and_group_owners(queryset, query_data)

        return queryset


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "feature",
                openapi.IN_QUERY,
                "ID of the feature to filter by.",
                required=False,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "feature_name",
                openapi.IN_QUERY,
                "Name of the feature to filter by.",
                required=False,
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "anyIdentity",
                openapi.IN_QUERY,
                "Pass any value to get results that have an identity override. "
                "Do not pass for default behaviour.",
                required=False,
                type=openapi.TYPE_STRING,
            ),
        ]
    ),
)
class BaseFeatureStateViewSet(viewsets.ModelViewSet):
    """
    View set to manage feature states. Nested beneath environments and environments + identities
    to allow for filtering on both.
    """

    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    # Override serializer class to show correct information in docs
    def get_serializer_class(self):
        if self.action == "list":
            return FeatureStateSerializerWithIdentity
        elif self.action in ["retrieve", "update", "create"]:
            return FeatureStateSerializerBasic
        else:
            return FeatureStateSerializerCreate

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.action in ["update", "create"]:
            context["environment"] = self.get_environment_from_request()
        return context

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        if getattr(self, "swagger_fake_view", False):
            return FeatureState.objects.none()

        environment_api_key = self.kwargs["environment_api_key"]

        try:
            environment = Environment.objects.get(api_key=environment_api_key)
            queryset = get_environment_flags_queryset(
                environment=environment,
                feature_name=self.request.query_params.get("feature_name"),
            )
            queryset = self._apply_query_param_filters(queryset)

            if self.action == "list":
                queryset = queryset.prefetch_related(
                    "multivariate_feature_state_values"
                )

            return queryset.select_related("feature_state_value", "identity", "feature")
        except Environment.DoesNotExist:
            raise NotFound("Environment not found.")

    def _apply_query_param_filters(self, queryset: QuerySet) -> QuerySet:
        if self.request.query_params.get("feature"):
            queryset = queryset.filter(
                feature__id=int(self.request.query_params["feature"])
            )
        return queryset

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        return environment

    def create(self, request, *args, **kwargs):
        """
        DEPRECATED: please use `/features/featurestates/` instead.
        Override create method to add environment and identity (if present) from URL parameters.
        """
        data = request.data
        if "feature" not in data:
            error = {"detail": "Feature not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment = self.get_environment_from_request()
        data["environment"] = environment.id

        identity_pk = self.kwargs.get("identity_pk")
        if identity_pk:
            data["identity"] = identity_pk

        serializer = self.get_serializer(data=data)

        if serializer.is_valid(raise_exception=True):
            feature_state = serializer.save()
            headers = self.get_success_headers(serializer.data)

            if "feature_state_value" in data:
                self.update_feature_state_value(
                    data["feature_state_value"], feature_state
                )

            return Response(
                FeatureStateSerializerBasic(feature_state).data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )

    def update(self, request, *args, **kwargs):
        """
        Override update method to always assume update request is partial and create / update
        feature state value.
        """
        feature_state_to_update = self.get_object()
        feature_state_data = request.data

        # Check if feature state value was provided with request data. If so, create / update
        # feature state value object and associate with feature state.
        if "feature_state_value" in feature_state_data:
            feature_state_value = self.update_feature_state_value(
                feature_state_data["feature_state_value"], feature_state_to_update
            )

            if isinstance(feature_state_value, Response):
                return feature_state_value

            feature_state_data["feature_state_value"] = feature_state_value.id

        serializer = self.get_serializer(
            feature_state_to_update, data=feature_state_data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(feature_state_to_update, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # refresh the instance from the database.
            feature_state_to_update = self.get_object()
            serializer = self.get_serializer(feature_state_to_update)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update as overridden update method assumes partial True for all requests.
        """
        return self.update(request, *args, **kwargs)

    def update_feature_state_value(self, value, feature_state):
        feature_state_value_dict = feature_state.generate_feature_state_value_data(
            value
        )

        if hasattr(feature_state, "feature_state_value"):
            feature_state_value_serializer = FeatureStateValueSerializer(
                instance=feature_state.feature_state_value,
                data=feature_state_value_dict,
            )
        else:
            data = {**feature_state_value_dict, "feature_state": feature_state.id}
            feature_state_value_serializer = FeatureStateValueSerializer(data=data)

        if feature_state_value_serializer.is_valid():
            feature_state_value = feature_state_value_serializer.save()
        else:
            return Response(
                feature_state_value_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return feature_state_value


class EnvironmentFeatureStateViewSet(BaseFeatureStateViewSet):
    permission_classes = [EnvironmentFeatureStatePermissions]

    def get_queryset(self):
        queryset = super().get_queryset().filter(feature_segment=None)
        if "anyIdentity" in self.request.query_params:
            # TODO: deprecate anyIdentity query parameter
            return queryset.exclude(identity=None)
        return queryset.filter(identity=None)

    def get_serializer_class(self):
        if self.action == "create_new_version":
            return FeatureStateSerializerBasic
        return super().get_serializer_class()


class IdentityFeatureStateViewSet(BaseFeatureStateViewSet):
    permission_classes = [IsAuthenticated, IdentityFeatureStatePermissions]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return FeatureState.objects.none()

        return super().get_queryset().filter(identity__pk=self.kwargs["identity_pk"])

    @action(methods=["GET"], detail=False)
    def all(self, request, *args, **kwargs):
        identity = get_object_or_404(Identity, pk=self.kwargs["identity_pk"])
        feature_states = identity.get_all_feature_states()

        serializer = IdentityAllFeatureStatesSerializer(
            instance=feature_states,
            many=True,
            context={
                "request": request,
                "identity": identity,
                "environment_api_key": identity.environment.api_key,
            },
        )

        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=IdentitySourceIdentityRequestSerializer(),
        responses={200: IdentityAllFeatureStatesSerializer(many=True)},
    )
    @action(methods=["POST"], detail=False, url_path="clone-from-given-identity")
    def clone_from_given_identity(self, request, *args, **kwargs) -> Response:
        """
        Clone feature states from a given source identity.
        """
        serializer = IdentitySourceIdentityRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        # Get and validate source and target identities
        target_identity = get_object_or_404(
            queryset=Identity, pk=self.kwargs["identity_pk"]
        )
        source_identity = get_object_or_404(
            queryset=Identity, pk=request.data.get("source_identity_id")
        )

        # Clone feature states
        FeatureState.copy_identity_feature_states(
            target_identity=target_identity, source_identity=source_identity
        )

        return self.all(request, *args, **kwargs)


@method_decorator(
    name="list",
    decorator=swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "environment",
                openapi.IN_QUERY,
                "ID of the environment.",
                required=True,
                type=openapi.TYPE_INTEGER,
            ),
        ]
    ),
)
class SimpleFeatureStateViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = WritableNestedFeatureStateSerializer
    permission_classes = [FeatureStatePermissions]
    filterset_fields = ["environment", "feature", "feature_segment"]

    def get_queryset(self):
        if not self.action == "list":
            return FeatureState.objects.all()

        try:
            if not (environment_id := self.request.query_params.get("environment")):
                raise ValidationError("'environment' GET parameter is required.")

            environment = get_object_or_404(Environment, id=environment_id)
            queryset = get_environment_flags_queryset(environment=environment)
            return queryset.select_related("feature_state_value").prefetch_related(
                "multivariate_feature_state_values"
            )
        except Environment.DoesNotExist:
            raise NotFound("Environment not found.")


@swagger_auto_schema(
    responses={200: WritableNestedFeatureStateSerializer()}, method="get"
)
@api_view(["GET"])
def get_feature_state_by_uuid(request, uuid):
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = FeatureState.objects.filter(
        feature__project__in=accessible_projects
    ).select_related("feature_state_value")
    feature_state = get_object_or_404(qs, uuid=uuid)
    serializer = WritableNestedFeatureStateSerializer(instance=feature_state)
    return Response(serializer.data)


class SDKFeatureStates(GenericAPIView):
    serializer_class = SDKFeatureStateSerializer
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
    renderer_classes = [JSONRenderer]
    pagination_class = None
    throttle_classes = []

    @swagger_auto_schema(
        query_serializer=SDKFeatureStatesQuerySerializer(),
        responses={200: FeatureStateSerializerFull(many=True)},
    )
    @method_decorator(
        cache_page(
            timeout=settings.GET_FLAGS_ENDPOINT_CACHE_SECONDS,
            cache=settings.GET_FLAGS_ENDPOINT_CACHE_NAME,
        )
    )
    def get(self, request, identifier=None, *args, **kwargs):
        """
        USING THIS ENDPOINT WITH AN IDENTIFIER IS DEPRECATED.
        Please use `/identities/?identifier=<identifier>` instead.
        ---
        Note that when providing the `feature` query argument, this endpoint will
        return either a single object or a 404 (if the feature does not exist) rather
        than a list.
        """
        if identifier:
            return self._get_flags_response_with_identifier(request, identifier)

        if "feature" in request.GET:
            feature_states = get_environment_flags_list(
                environment=request.environment,
                feature_name=request.GET["feature"],
                additional_filters=self._additional_filters,
            )
            if len(feature_states) != 1:
                # TODO: what if more than one?
                return Response(
                    {"detail": "Given feature not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(self.get_serializer(feature_states[0]).data)

        if settings.CACHE_FLAGS_SECONDS > 0:
            data = self._get_flags_from_cache(request.environment)
        else:
            data = self.get_serializer(
                get_environment_flags_list(
                    environment=request.environment,
                    additional_filters=self._additional_filters,
                ),
                many=True,
            ).data

        updated_at = self.request.environment.updated_at
        return Response(
            data,
            headers={FLAGSMITH_UPDATED_AT_HEADER: updated_at.timestamp()},
        )

    @property
    def _additional_filters(self) -> Q:
        filters = Q(feature_segment=None, identity=None)

        if self.request.environment.get_hide_disabled_flags() is True:
            return filters & Q(enabled=True)

        if self.request.originated_from is RequestOrigin.CLIENT:
            return filters & Q(feature__is_server_key_only=False)

        return filters

    def _get_flags_from_cache(self, environment):
        data = flags_cache.get(environment.api_key)
        if not data:
            data = self.get_serializer(
                get_environment_flags_list(
                    environment=environment,
                    additional_filters=self._additional_filters,
                ),
                many=True,
            ).data
            flags_cache.set(environment.api_key, data, settings.CACHE_FLAGS_SECONDS)

        return data

    def _get_flags_response_with_identifier(self, request, identifier):
        identity, _ = Identity.objects.get_or_create(
            identifier=identifier, environment=request.environment
        )

        kwargs = {
            "identity": identity,
            "environment": request.environment,
            "feature_segment": None,
        }

        if "feature" in request.GET:
            kwargs["feature__name__iexact"] = request.GET["feature"]
            try:
                feature_state = identity.get_all_feature_states().get(
                    feature__name__iexact=kwargs["feature__name__iexact"],
                )
            except FeatureState.DoesNotExist:
                return Response(
                    {"detail": "Given feature not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                self.get_serializer(feature_state).data, status=status.HTTP_200_OK
            )

        flags = self.get_serializer(identity.get_all_feature_states(), many=True)
        return Response(flags.data, status=status.HTTP_200_OK)


def organisation_has_got_feature(request, organisation):
    """
    Helper method to set flag against organisation to confirm that they've requested their
    feature states for analytics purposes

    :param request: HTTP request
    :return: True if value set. None otherwise.
    """
    if organisation.has_requested_features:
        return None

    referer = request.META.get("HTTP_REFERER")
    if not referer or "bullet-train.io" in referer:
        return None
    else:
        organisation.has_requested_features = True
        organisation.save()
        return True


@swagger_auto_schema(
    method="POST",
    request_body=CreateSegmentOverrideFeatureStateSerializer(),
    responses={201: CreateSegmentOverrideFeatureStateSerializer()},
)
@api_view(["POST"])
@permission_classes([CreateSegmentOverridePermissions])
def create_segment_override(
    request: Request, environment_api_key: str, feature_pk: int
):
    environment = get_object_or_404(Environment, api_key=environment_api_key)
    feature = get_object_or_404(Feature, project=environment.project, pk=feature_pk)

    serializer = CreateSegmentOverrideFeatureStateSerializer(
        data=request.data, context={"environment": environment, "feature": feature}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(environment=environment, feature=feature)
    return Response(serializer.data, status=201)
