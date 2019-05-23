# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import namedtuple

import coreapi
from rest_framework import viewsets, status
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from util.util import get_user_permitted_identities, get_user_permitted_environments, get_user_permitted_projects
from .models import Environment, Identity, Trait
from .serializers import EnvironmentSerializerLight, IdentitySerializer, TraitSerializerBasic, TraitSerializerFull, \
    IdentitySerializerTraitFlags, AuditLogSerializer


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

    def create(self, request, *args, **kwargs):
        project_pk = request.data.get('project')

        if not project_pk:
            return Response(data = {"detail": "No project provided"}, status=status.HTTP_400_BAD_REQUEST)

        get_object_or_404(get_user_permitted_projects(self.request.user), pk=project_pk)

        return super().create(request, *args, **kwargs)


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
        environment = self.get_environment_from_request()
        user_permitted_identities = get_user_permitted_identities(self.request.user)

        return user_permitted_identities.filter(environment__api_key=environment.api_key)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        environment = Environment.objects.get(api_key=self.kwargs['environment_api_key'])
        return environment

    def create(self, request, *args, **kwargs):
        environment = self.get_environment_from_request()
        if environment.project.organisation not in request.user.organisations.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
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
    Delete a trait for given identity
    """

    serializer_class = TraitSerializerFull

    def get_queryset(self):
        """
        Override queryset to filter based on provided URL parameters.
        """
        environment_api_key = self.kwargs['environment_api_key']
        identifier = self.kwargs.get('identity_identifier')
        environment = get_user_permitted_environments(self.request.user).get(api_key=environment_api_key)

        if identifier:
            identity = Identity.objects.get(identifier=identifier, environment=environment)
        else:
            identity = None

        return Trait.objects.filter(identity=identity)

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
        environment = self.get_environment_from_request()
        if environment.project.organisation not in self.request.user.organisations.all():
            return Response(status=status.HTTP_403_FORBIDDEN)

        identifier = self.kwargs.get('identity_identifier', None)

        # check if identity in data or in request
        if 'identity' not in data and not identifier:
            error = {"detail": "Identity not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # TODO: do we give priority to request identity or data?
        # Override with request identity
        if identifier:
            identity = self.get_identity_from_request(environment)
            data['identity'] = identity.id

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Override update method to always assume update request is partial and create / update
        trait value.
        """
        trait_to_update = self.get_object()
        trait_data = request.data

        # Check if trait value was provided with request data. If so, we need to figure out value_type from
        # the given value and also use correct value field e.g. boolean_value, integer_value or
        # string_value, and override request data
        if 'trait_value' in trait_data:
            trait_data = trait_to_update.generate_trait_value_data(trait_data['trait_value'])

        serializer = TraitSerializerFull(trait_to_update, data=trait_data, partial=True)

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update as overridden update method assumes partial True for all requests.
        """
        return self.update(request, *args, **kwargs)


class SDKIdentities(GenericAPIView):
    # API to handle /api/v1/identities/ endpoint to return Flags and Traits for user Identity
    # if Identity does not exist it will create one, otherwise will fetch existing

    serializer_class = IdentitySerializerTraitFlags
    permission_classes = (AllowAny,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("X-Environment-Key", location="header",
                          description="API Key for an Environment"),
            coreapi.Field("identifier", location="path", required=True,
                          description="Identity user identifier")
        ]
    )

    # identifier is in a path parameter
    def get(self, request, identifier, *args, **kwargs):
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment_key = request.META['HTTP_X_ENVIRONMENT_KEY']
        environment = Environment.objects.get(api_key=environment_key)

        # if we have identifier fetch, or create if does not exist
        if identifier:

            identity, _ = Identity.objects.get_or_create(
                identifier=identifier,
                environment=environment,
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

        if identity:
            traits_data = identity.get_all_user_traits()
            # traits_data = self.get_serializer(identity.get_all_user_traits(), many=True)
            # return Response(traits.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"detail": "Given identifier not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # We need object type to pass into our IdentitySerializerTraitFlags
        IdentityTraitFlags = namedtuple('IdentityTraitFlags', ('flags', 'traits'))
        traitsAndFlags = IdentityTraitFlags(
            flags=identity.get_all_feature_states(),
            traits=traits_data,
        )

        serializer = IdentitySerializerTraitFlags(traitsAndFlags)

        return Response(serializer.data, status=status.HTTP_200_OK)


class SDKTraits(GenericAPIView):
    # API to handle /api/v1/identities/<identifier>/traits/<trait_key> endpoints
    # if Identity or Trait does not exist it will create one, otherwise will fetch existing

    serializer_class = TraitSerializerBasic
    permission_classes = (AllowAny,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("X-Environment-Key", location="header",
                          description="API Key for an Environment"),
            coreapi.Field("identifier", location="path", required=True,
                          description="Identity user identifier"),
            coreapi.Field("trait_key", location="path", required=True,
                          description="User trait unique key")
        ]
    )

    def post(self, request, identifier, trait_key, *args, **kwargs):
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment_key = request.META['HTTP_X_ENVIRONMENT_KEY']
        environment = Environment.objects.get(api_key=environment_key)
        trait_data = request.data

        if 'trait_value' not in trait_data:
            error = {"detail": "Trait value not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # if we have identifier fetch, or create if does not exist
        if identifier:
            identity, _ = Identity.objects.get_or_create(
                identifier=identifier,
                environment=environment,
            )

        else:
            return Response(
                {"detail": "Missing identifier"},
                status=status.HTTP_400_BAD_REQUEST
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
                {"detail": "Missing trait key"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if trait and 'trait_value' in trait_data:
            # Check if trait value was provided with request data. If so, we need to figure out value_type from
            # the given value and also use correct value field e.g. boolean_value, integer_value or
            # string_value, and override request data
            trait_data = trait.generate_trait_value_data(trait_data['trait_value'])

            trait_full_serializer = TraitSerializerFull(trait, data=trait_data, partial=True)

            if trait_full_serializer.is_valid():
                trait_full_serializer.save()
                return Response(self.get_serializer(trait).data, status=status.HTTP_200_OK)
            else:
                return Response(trait_full_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"detail": "Failed to update user trait"}, status=status.HTTP_400_BAD_REQUEST)

class AuditLogViewSet(viewsets.ModelViewSet):
    """
    list:
    Get all audit logs within specified environment

    create:
    Create audit log within specified environment

    retrieve:
    Get specific audit log within specified environment
    """

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        environment = self.get_environment_from_request()
        user_permitted_identities = get_user_permitted_identities(self.request.user)

        return user_permitted_identities.filter(environment__api_key=environment.api_key)

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        environment = Environment.objects.get(api_key=self.kwargs['environment_api_key'])
        return environment

    def create(self, request, *args, **kwargs):
        environment = self.get_environment_from_request()
        if environment.project.organisation not in request.user.organisations.all():
            return Response(status=status.HTTP_403_FORBIDDEN)
        data = request.data
        data['environment'] = environment.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
