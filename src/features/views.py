import logging

import coreapi
from django.conf import settings
from django.core.cache import caches
from django.utils.decorators import method_decorator
from drf_yasg2 import openapi
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from app_analytics.influxdb_wrapper import get_multiple_event_list_for_feature
from audit.models import (
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from environments.authentication import EnvironmentKeyAuthentication
from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.permissions import (
    EnvironmentKeyPermissions,
    NestedEnvironmentPermissions,
)
from projects.models import Project
from .models import FeatureState, Feature
from .permissions import FeaturePermissions, FeatureStatePermissions
from .serializers import (
    CreateFeatureSerializer,
    FeatureInfluxDataSerializer,
    FeatureSerializer,
    FeatureStateSerializerBasic,
    FeatureStateSerializerCreate,
    FeatureStateSerializerFull,
    FeatureStateSerializerWithIdentity,
    FeatureStateValueSerializer,
    FeatureWithTagsSerializer,
    UpdateFeatureSerializer,
    GetInfluxDataQuerySerializer,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

flags_cache = caches[settings.FLAGS_CACHE_LOCATION]


class FeatureViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, FeaturePermissions]

    def get_serializer_class(self):
        return {
            "list": FeatureWithTagsSerializer,
            "create": CreateFeatureSerializer,
            "update": UpdateFeatureSerializer,
            "partial_update": UpdateFeatureSerializer,
        }.get(self.action, FeatureSerializer)

    def get_queryset(self):
        user_projects = self.request.user.get_permitted_projects(["VIEW_PROJECT"])
        project = get_object_or_404(user_projects, pk=self.kwargs["project_pk"])

        return project.features.all()

    def create(self, request, *args, **kwargs):
        project_id = request.data.get("project")
        project = get_object_or_404(Project, pk=project_id)

        if project.organisation not in request.user.organisations.all():
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        query_serializer=GetInfluxDataQuerySerializer(),
        responses={200: FeatureInfluxDataSerializer()},
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
class FeatureStateViewSet(viewsets.ModelViewSet):
    """
    View set to manage feature states. Nested beneath environments and environments + identities
    to allow for filtering on both.
    """

    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]

    # Override serializer class to show correct information in docs
    def get_serializer_class(self):
        if self.action == "list":
            return FeatureStateSerializerWithIdentity
        elif self.action in ["retrieve", "update"]:
            return FeatureStateSerializerBasic
        else:
            return FeatureStateSerializerCreate

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        environment_api_key = self.kwargs["environment_api_key"]
        identity_pk = self.kwargs.get("identity_pk")
        environment = get_object_or_404(
            self.request.user.get_permitted_environments(["VIEW_ENVIRONMENT"]),
            api_key=environment_api_key,
        )

        queryset = FeatureState.objects.filter(
            environment=environment, feature_segment=None
        )

        if identity_pk:
            queryset = queryset.filter(identity__pk=identity_pk)
        elif "anyIdentity" in self.request.query_params:
            queryset = queryset.exclude(identity=None)
        else:
            queryset = queryset.filter(identity=None, feature_segment=None)

        if self.request.query_params.get("feature"):
            queryset = queryset.filter(
                feature__id=int(self.request.query_params.get("feature"))
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

    def get_identity_from_request(self, environment):
        """
        Get identity object from URL parameters in request.
        """
        identity = Identity.objects.get(pk=self.kwargs["identity_pk"])
        return identity

    def create(self, request, *args, **kwargs):
        """
        DEPRECATED: please use `/features/featurestates/` instead.
        Override create method to add environment and identity (if present) from URL parameters.
        """
        data = request.data
        environment = self.get_environment_from_request()
        if (
            environment.project.organisation
            not in self.request.user.organisations.all()
        ):
            return Response(status.HTTP_403_FORBIDDEN)

        data["environment"] = environment.id

        if "feature" not in data:
            error = {"detail": "Feature not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        feature_id = int(data["feature"])

        if feature_id not in [
            feature.id for feature in environment.project.features.all()
        ]:
            error = {"detail": "Feature does not exist in project"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        identity_pk = self.kwargs.get("identity_pk")
        if identity_pk:
            data["identity"] = identity_pk

        serializer = FeatureStateSerializerBasic(
            data=data, context=self.get_serializer_context()
        )
        if serializer.is_valid():
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
        else:
            logger.error(serializer.errors)
            error = {"detail": "Couldn't create feature state."}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

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
        self.perform_update(serializer)

        if getattr(feature_state_to_update, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # refresh the instance from the database.
            feature_state_to_update = self.get_object()
            serializer = self.get_serializer(feature_state_to_update)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        feature_state = get_object_or_404(self.get_queryset(), pk=kwargs.get("pk"))
        res = super(FeatureStateViewSet, self).destroy(request, *args, **kwargs)
        if res.status_code == status.HTTP_204_NO_CONTENT:
            self._create_deleted_feature_state_audit_log(feature_state)
        return res

    def _create_deleted_feature_state_audit_log(self, feature_state):
        message = IDENTITY_FEATURE_STATE_DELETED_MESSAGE % (
            feature_state.feature.name,
            feature_state.identity.identifier,
        )

        AuditLog.objects.create(
            author=getattr(self.request, "user", None),
            related_object_id=feature_state.id,
            related_object_type=RelatedObjectType.FEATURE_STATE.name,
            environment=feature_state.environment,
            project=feature_state.environment.project,
            log=message,
        )

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


class FeatureStateCreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = FeatureStateSerializerBasic
    permission_classes = [FeatureStatePermissions]


class SDKFeatureStates(GenericAPIView):
    serializer_class = FeatureStateSerializerFull
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field(
                "X-Environment-Key",
                location="header",
                description="API Key for an Environment",
            ),
            coreapi.Field(
                "feature",
                location="query",
                description="Name of the feature to get the state of",
            ),
        ]
    )

    def get(self, request, identifier=None, *args, **kwargs):
        """
        USING THIS ENDPOINT WITH AN IDENTIFIER IS DEPRECATED.
        Please use `/identities/?identifier=<identifier>` instead.
        """
        if identifier:
            return self._get_flags_response_with_identifier(request, identifier)

        filter_args = {
            "identity": None,
            "environment": request.environment,
            "feature_segment": None,
        }

        if "feature" in request.GET:
            filter_args["feature__name__iexact"] = request.GET["feature"]
            try:
                feature_state = FeatureState.objects.get(**filter_args)
            except FeatureState.DoesNotExist:
                return Response(
                    {"detail": "Given feature not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(self.get_serializer(feature_state).data)

        if settings.CACHE_FLAGS_SECONDS > 0:
            data = self._get_flags_from_cache(filter_args, request.environment)
        else:
            data = self.get_serializer(
                # ignore disabled Flags when project hide_disabled_flags is enabled
                FeatureState.objects.filter(**filter_args)
                .exclude(
                    feature__project__hide_disabled_flags=True,
                    enabled=False,
                )
                .select_related("feature", "feature_state_value"),
                many=True,
            ).data

        return Response(data)

    def _get_flags_from_cache(self, filter_args, environment):
        data = flags_cache.get(environment.api_key)
        if not data:
            data = self.get_serializer(
                # ignore disabled Flags when project hide_disabled_flags is enabled
                FeatureState.objects.filter(**filter_args)
                .exclude(
                    feature__project__hide_disabled_flags=True,
                    enabled=False,
                )
                .select_related("feature", "feature_state_value"),
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
