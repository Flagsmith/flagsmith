# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from collections import namedtuple

import coreapi
from rest_framework import viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from .models import Environment, Identity, Trait
from features.models import FeatureState
from .serializers import EnvironmentSerializerLight, IdentitySerializer, TraitSerializer, TraitSerializerUpdate,\
    IdentitySerializerTraitFlags


class EnvironmentViewSet(viewsets.ModelViewSet):
    """
    list:
    Get all environments for current user

    create:
    Create a new environment

    retrieve:
    Get a specific environment

    update:
    Update specific environment

    partial_update:
    Partially update specific environment

    delete:
    Delete an environment
    """
    serializer_class = EnvironmentSerializerLight
    lookup_field = 'api_key'

    def get_queryset(self):
        queryset = Environment.objects.filter(
            project__in=self.request.user.organisations.values_list('projects', flat=True)
        )

        return queryset


class IdentityViewSet(viewsets.ModelViewSet):
    """
    list:
    Get all identities within specified environment

    create:
    Create identity within specified environment

    retrieve:
    Get specific identity within specified environment

    update:
    Update an identity within specified environment

    partial_update:
    Partially update an identity within specified environment

    delete:
    Delete an identity within specified environment
    """

    serializer_class = IdentitySerializer
    lookup_field = 'identifier'

    def get_queryset(self):
        env_key = self.kwargs['environment_api_key']
        return Identity.objects.filter(environment__api_key=env_key)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        environment = Environment.objects.get(api_key=self.kwargs['environment_api_key'])
        return environment

    def create(self, request, *args, **kwargs):
        environment = self.get_environment_from_request()
        data = request.data
        data['environment'] = environment.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TraitViewSet(viewsets.ModelViewSet):
    """
    list:
    Get all traits for given identity

    create:
    Create trait for identity

    retrieve:
    Get specific trait for specified identity

    update:
    Update a trait for specified identity

    partial_update:
    Partially update a trait for given identity

    delete:
    Delete an identity for given identity
    """

    serializer_class = TraitSerializer
    lookup_field = 'trait_key'

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        environment_api_key = self.kwargs['environment_api_key']
        identifier = self.kwargs.get('identity_identifier')
        environment = Environment.objects.get(api_key=environment_api_key)

        if identifier:
            identity = Identity.objects.get(identifier=identifier, environment=environment)
        else:
            identity = None

        return Trait.objects.filter(environment=environment, identity=identity)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        return Environment.objects.get(api_key=self.kwargs['environment_api_key'])

    def get_identity_from_request(self, environment):
        """
        Get identity object from URL parameters in request.
        """
        return Identity.objects.get(identifier=self.kwargs['identity_identifier'], environment=environment)

    def create(self, request, *args, **kwargs):
        """
        Override create method to add identity (if present) from URL parameters.
        """
        data = request.data

        if 'identity' not in data:
            error = {"detail": "Identity not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Override update method to always assume update request is partial and create / update
        feature state value.
        """
        trait_to_update = self.get_object()
        trait_data = request.data


class SDKIdentities(GenericAPIView):
    # API to handle /api/v1/identities/ endpoint to return Flags and Traits for user Identity

    serializer_class = IdentitySerializerTraitFlags
    permission_classes = (AllowAny,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("X-Environment-Key", location="header",
                          description="API Key for an Environment"),
            coreapi.Field("identifier", location="path",
                          description="Identity user identifier")
        ]
    )

    # identifier is an optional path parameter
    def get(self, request, identifier=None, *args, **kwargs):
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment_key = request.META['HTTP_X_ENVIRONMENT_KEY']
        environment = Environment.objects.get(api_key=environment_key)

        # if identifier:
        # Thread(track_event(environment.project.organisation.name, "identity_flags")).start()
        #
        # identity, _ = Identity.objects.get_or_create(
        #     identifier=identifier,
        #     environment=environment,
        # )
        # else:
        # Thread(track_event(environment.project.organisation.name, "flags")).start()
        # identity = None

        if identifier:
            try:
                identity = Identity.objects.get(identifier=identifier, environment=environment)
            except Identity.DoesNotExist:
                return Response(
                    {"detail": "Given identifier not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                {"detail": "Missing identifier"},
                status=status.HTTP_400_BAD_REQUEST
            )

        kwargs = {
            'identity': identity,
            'environment': environment,
        }

        # if 'feature' in request.GET:
        #     kwargs['feature__name__iexact'] = request.GET['feature']
        #     try:
        #         if identity:
        #             feature_state = identity.get_all_feature_states().get(
        #                 feature__name__iexact=kwargs['feature__name__iexact'],
        #             )
        #         else:
        #             feature_state = FeatureState.objects.get(**kwargs)
        #     except FeatureState.DoesNotExist:
        #         return Response(
        #             {"detail": "Given feature not found"},
        #             status=status.HTTP_404_NOT_FOUND
        #         )
        #
        #     return Response(self.get_serializer(feature_state).data, status=status.HTTP_200_OK)

        if identity:
            traits_data = identity.get_all_user_traits()
            # traits = self.get_serializer(identity.get_all_user_traits(), many=True)
            # return Response(traits.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Given identifier not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # We need object type to pass into our IdentitySerializerTraitFlags
        IdentityTraitFlags = namedtuple('IdentityTraitFlags', ('flags', 'traits'))
        traitsAndFlags = IdentityTraitFlags(
            flags=FeatureState.objects.filter(**kwargs),
            traits=traits_data,
        )

        serializer = IdentitySerializerTraitFlags(traitsAndFlags)

        # environment_flags = FeatureState.objects.filter(**kwargs)
        # self.get_serializer(traits, environment_flags)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class SDKTraits(GenericAPIView):
    # API to handle /api/v1/identities/ endpoints

    serializer_class = TraitSerializerUpdate
    permission_classes = (AllowAny,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("X-Environment-Key", location="header",
                          description="API Key for an Environment"),
            coreapi.Field("identifier", location="path",
                          description="Identity user identifier"),
            coreapi.Field("traitkey", location="path",
                          description="User trait unique key value")
        ]
    )

    def put(self, request, identifier=None, traitkey=None, *args, **kwargs):
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment_key = request.META['HTTP_X_ENVIRONMENT_KEY']
        environment = Environment.objects.get(api_key=environment_key)
