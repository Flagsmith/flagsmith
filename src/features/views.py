import coreapi
from rest_framework import status, viewsets
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from environments.models import Environment, Identity
from projects.models import Project
from .models import FeatureState, Feature
from .serializers import FeatureStateSerializerBasic, FeatureStateSerializerFull, \
    FeatureStateSerializerCreate, CreateFeatureSerializer, FeatureSerializer


class FeatureViewSet(viewsets.ModelViewSet):
    queryset = Feature.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateFeatureSerializer
        else:
            return FeatureSerializer

    def get_queryset(self):
        project = Project.objects.get(pk=self.kwargs['project_pk'])
        return project.features.all()


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

    def create(self, request, *args, **kwargs):
        """
        Override create method to add environment and identity (if present) from URL parameters.
        """
        data = request.data
        environment = self.get_environment_from_request()
        data['environment'] = environment.id

        if not self.kwargs.get('identity_identifier', None):
            error = {"detail": "Creating feature state must include an identity"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        identity = self.get_identity_from_request(environment)
        data['identity'] = identity.id

        if not self.validate_feature_provided_and_exists_in_project(environment.project):
            error = {"detail": "Feature not provided or doesn't exist in project"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        serializer = FeatureStateSerializerBasic(data=data)
        if serializer.is_valid():
            feature_state = serializer.save()
            headers = self.get_success_headers(serializer.data)

            if 'feature_state_value' in data:
                feature_state.create_or_update_feature_state_value(data['feature_state_value'])

            return Response(FeatureStateSerializerBasic(feature_state).data,
                            status=status.HTTP_201_CREATED, headers=headers)
        else:
            error = {"detail": "Couldn't create feature state."}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        environment_api_key = self.kwargs['environment_api_key']
        identifier = self.kwargs.get('identity_identifier', None)
        environment = Environment.objects.get(api_key=environment_api_key)

        if identifier:
            identity = Identity.objects.get(identifier=identifier, environment=environment)
        else:
            identity = None

        return FeatureState.objects.filter(environment=environment, identity=identity)

    # Override serializer class to show correct information in docs
    def get_serializer_class(self):

        if self.action not in ['list', 'retrieve']:
            return FeatureStateSerializerCreate
        else:
            return FeatureStateSerializerBasic

    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update as overridden update method assumes partial True for all requests.
        """
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Override update method to always assume update request is partial and create / update
        feature state value.
        """
        feature_state_to_update = self.get_object()
        feature_state_data = request.data

        # Create / update feature state value if provided
        if 'feature_state_value' in feature_state_data:
            feature_state_value_data = feature_state_data.pop('feature_state_value')
            feature_state_to_update.create_or_update_feature_state_value(feature_state_value_data)

        serializer = FeatureStateSerializerBasic(feature_state_to_update, data=feature_state_data,
                                                 partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(feature_state_to_update, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # refresh the instance from the database.
            feature_state_to_update = self.get_object()
            serializer = self.get_serializer(feature_state_to_update)

        return Response(serializer.data)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        environment = Environment.objects.get(api_key=self.kwargs['environment_api_key'])
        return environment

    def get_identity_from_request(self, environment):
        """
        Get identity object from URL parameters in request.
        """
        identity = Identity.objects.get(identifier=self.kwargs['identity_identifier'],
                                        environment=environment)
        return identity

    def validate_feature_provided_and_exists_in_project(self, project):
        data = self.request.data

        if 'feature' not in self.request.data:
            return False

        feature_id = int(data['feature'])

        if feature_id not in [feature.id for feature in project.features.all()]:
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
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment = get_object_or_404(Environment, api_key=request.META['HTTP_X_ENVIRONMENT_KEY'])

        if identifier:
            try:
                identity = Identity.objects.get(identifier=identifier, environment=environment)
            except Identity.DoesNotExist:
                identity = Identity.objects.create(identifier=identifier, environment=environment)

            if 'feature' in request.GET:
                try:
                    feature = Feature.objects.get(name__iexact=request.GET['feature'],
                                                  project=environment.project)
                    feature_state = FeatureState.objects.get(identity=identity,
                                                             feature=feature,
                                                             environment=environment)
                    return Response(self.get_serializer(feature_state).data,
                                    status=status.HTTP_200_OK)

                except Feature.DoesNotExist:
                    error = {"detail": "Given feature not found"}
                    return Response(error, status=status.HTTP_404_NOT_FOUND)

                except FeatureState.DoesNotExist:
                    feature_state = FeatureState.objects.get(feature=feature,
                                                             environment=environment,
                                                             identity=None)
                    return Response(self.get_serializer(feature_state).data,
                                    status=status.HTTP_200_OK)

            identity_flags, environment_flags = identity.get_all_feature_states()

            serialized_env_flags = self.get_serializer(environment_flags, many=True)
            serialized_id_flags = self.get_serializer(identity_flags, many=True)

            return Response(serialized_env_flags.data + serialized_id_flags.data,
                            status=status.HTTP_200_OK)

        else:
            if 'feature' in request.GET:
                try:
                    feature = Feature.objects.get(name__iexact=request.GET['feature'],
                                                  project=environment.project)
                except Feature.DoesNotExist:
                    error = {"detail": "Given feature not found"}
                    return Response(error, status=status.HTTP_404_NOT_FOUND)

                environment_flag = FeatureState.objects.get(environment=environment,
                                                            identity=None,
                                                            feature=feature)
                return Response(self.get_serializer(environment_flag).data,
                                status=status.HTTP_200_OK)
            else:
                environment_flags = FeatureState.objects.filter(environment=environment,
                                                                identity=None)
                return Response(self.get_serializer(environment_flags, many=True).data,
                                status=status.HTTP_200_OK)
