import logging

import coreapi
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from analytics.track import track_event
from audit.models import AuditLog, RelatedObjectType, FEATURE_SEGMENT_UPDATED_MESSAGE
from environments.models import Environment, Identity
from projects.models import Project
from util.util import get_user_permitted_projects, get_user_permitted_environments
from .models import FeatureState, Feature, FeatureSegment
from .serializers import FeatureStateSerializerBasic, FeatureStateSerializerFull, \
    FeatureStateSerializerCreate, CreateFeatureSerializer, FeatureSerializer, \
    FeatureStateValueSerializer, FeatureSegmentCreateSerializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return CreateFeatureSerializer
        else:
            return FeatureSerializer

    def get_queryset(self):
        user_projects = get_user_permitted_projects(self.request.user)
        project = get_object_or_404(user_projects, pk=self.kwargs['project_pk'])

        return project.features.all()

    def create(self, request, *args, **kwargs):
        project_id = request.data.get('project')
        project = Project.objects.get(pk=project_id)

        if project.organisation not in request.user.organisations.all():
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["POST"])
    @transaction.atomic
    def segments(self, request, *args, **kwargs):
        feature = self.get_object()
        # delete existing segments to avoid priority clashes, note method is transactional so will roll back on error
        FeatureSegment.objects.filter(feature=feature).delete()

        self._create_feature_segments(feature, request.data)
        self._create_feature_segments_audit_log()

        return Response(data=FeatureSerializer(instance=feature).data, status=status.HTTP_200_OK)

    @staticmethod
    def _create_feature_segments(feature, feature_segment_data):
        for feature_segment in feature_segment_data:
            feature_segment["feature"] = feature.id
            fs_serializer = FeatureSegmentCreateSerializer(data=feature_segment)
            if fs_serializer.is_valid(raise_exception=True):
                fs_serializer.save()

    def _create_feature_segments_audit_log(self):
        feature = self.get_object()
        message = FEATURE_SEGMENT_UPDATED_MESSAGE % feature.name
        AuditLog.objects.create(author=self.request.user, related_object_id=feature.id,
                                related_object_type=RelatedObjectType.FEATURE.name,
                                project=feature.project,
                                log=message)


class FeatureStateViewSet(viewsets.ModelViewSet):
    """
    View set to manage feature states. Nested beneath environments and environments + identities
    to allow for filtering on both.

    list:
    Get feature states for an environment or identity if provided

    create:
    Create feature state for an environment or identity if provided

    retrieve:
    Get specific feature state

    update:
    Update specific feature state

    partial_update:
    Partially update specific feature state

    delete:
    Delete specific feature state
    """

    # Override serializer class to show correct information in docs
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'update']:
            return FeatureStateSerializerBasic
        else:
            return FeatureStateSerializerCreate

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        environment_api_key = self.kwargs['environment_api_key']
        identity_pk = self.kwargs.get('identity_pk')
        environment = get_object_or_404(get_user_permitted_environments(self.request.user), api_key=environment_api_key)

        if identity_pk:
            identity = Identity.objects.get(pk=identity_pk)
        else:
            identity = None

        return FeatureState.objects.filter(environment=environment, identity=identity)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        environment = Environment.objects.get(
            api_key=self.kwargs['environment_api_key'])
        return environment

    def get_identity_from_request(self, environment):
        """
        Get identity object from URL parameters in request.
        """
        identity = Identity.objects.get(pk=self.kwargs['identity_pk'])
        return identity

    def create(self, request, *args, **kwargs):
        """
        DEPRECATED: please use `/features/featurestates/` instead.
        Override create method to add environment and identity (if present) from URL parameters.
        """
        data = request.data
        environment = self.get_environment_from_request()
        if environment.project.organisation not in self.request.user.organisations.all():
            return Response(status.HTTP_403_FORBIDDEN)

        data['environment'] = environment.id

        if 'feature' not in data:
            error = {"detail": "Feature not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        feature_id = int(data['feature'])

        if feature_id not in [feature.id for feature in environment.project.features.all()]:
            error = {"detail": "Feature does not exist in project"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        identity_pk = self.kwargs.get('identity_pk')
        if identity_pk:
            data['identity'] = identity_pk

        serializer = FeatureStateSerializerBasic(data=data)
        if serializer.is_valid():
            feature_state = serializer.save()
            headers = self.get_success_headers(serializer.data)

            if 'feature_state_value' in data:
                self.update_feature_state_value(feature_state.feature_state_value,
                                                data['feature_state_value'], feature_state)

            return Response(FeatureStateSerializerBasic(feature_state).data,
                            status=status.HTTP_201_CREATED, headers=headers)
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
        if 'feature_state_value' in feature_state_data:
            feature_state_value = self.update_feature_state_value(
                feature_state_to_update.feature_state_value,
                feature_state_data['feature_state_value'],
                feature_state_to_update
            )

            if isinstance(feature_state_value, Response):
                return feature_state_value

            feature_state_data['feature_state_value'] = feature_state_value.id

        serializer = self.get_serializer(feature_state_to_update, data=feature_state_data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(feature_state_to_update, '_prefetched_objects_cache', None):
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

    def update_feature_state_value(self, instance, value, feature_state):
        feature_state_value_dict = feature_state.generate_feature_state_value_data(
            value)

        feature_state_value_serializer = FeatureStateValueSerializer(
            instance=instance,
            data=feature_state_value_dict
        )

        if feature_state_value_serializer.is_valid():
            feature_state_value = feature_state_value_serializer.save()
        else:
            return Response(feature_state_value_serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        return feature_state_value


class FeatureStateCreateViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = FeatureStateSerializerBasic

    def create(self, request, *args, **kwargs):
        if not self._is_user_authorised(request):
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    @staticmethod
    def _is_user_authorised(request):
        data = request.data
        environment = get_object_or_404(Environment.objects.all(), pk=data.get('environment'))
        feature = get_object_or_404(Feature.objects.all(), pk=data.get('feature'))

        identity_pk = data.get('identity')
        if identity_pk:
            identity = get_object_or_404(Identity.objects.all(), pk=identity_pk)
            if identity.environment != environment:
                return False

        if environment.project.organisation not in request.user.organisations.all() or \
                feature.project.organisation != environment.project.organisation:
            return False

        return True


class SDKFeatureStates(GenericAPIView):
    serializer_class = FeatureStateSerializerFull
    permission_classes = (AllowAny,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("X-Environment-Key", location="header",
                          description="API Key for an Environment"),
            coreapi.Field("feature", location="query",
                          description="Name of the feature to get the state of")
        ]
    )

    def get(self, request, identifier=None, *args, **kwargs):
        """
        USING THIS ENDPOINT WITH AN IDENTIFIER IS DEPRECATED.
        Please use `/identities/?identifier=<identifier>` instead.
        """
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment_key = request.META['HTTP_X_ENVIRONMENT_KEY']
        try:
            environment = Environment.objects.select_related('project', 'project__organisation').get(
                api_key=environment_key)
        except ObjectDoesNotExist:
            error_details = "Environment not found for key: " + environment_key
            logger.error(error_details)
            error_response = {"error": error_details}

            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        if identifier:
            track_event(environment.project.organisation.get_unique_slug(), "identity_flags")

            identity, _ = Identity.objects.get_or_create(
                identifier=identifier,
                environment=environment,
            )
        else:
            track_event(environment.project.organisation.get_unique_slug(), "flags")
            identity = None

        kwargs = {
            'identity': identity,
            'environment': environment,
        }

        if 'feature' in request.GET:
            kwargs['feature__name__iexact'] = request.GET['feature']
            try:
                if identity:
                    feature_state = identity.get_all_feature_states().get(
                        feature__name__iexact=kwargs['feature__name__iexact'],
                    )
                else:
                    feature_state = FeatureState.objects.get(**kwargs)
            except FeatureState.DoesNotExist:
                return Response(
                    {"detail": "Given feature not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(self.get_serializer(feature_state).data, status=status.HTTP_200_OK)

        if identity:
            flags = self.get_serializer(
                identity.get_all_feature_states(), many=True)
            return Response(flags.data, status=status.HTTP_200_OK)

        environment_flags = FeatureState.objects.filter(**kwargs).select_related("feature", "feature_state_value")
        return Response(
            self.get_serializer(environment_flags, many=True).data,
            status=status.HTTP_200_OK
        )


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
