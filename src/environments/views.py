# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import coreapi
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from .models import Environment, Identity
from .serializers import EnvironmentSerializerLight, IdentitySerializer


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
        user_organisations = self.request.user.organisations.all()
        user_projects = []

        for user_org in user_organisations:
            for project in user_org.projects.all():
                user_projects.append(project.id)

        queryset = Environment.objects.filter(project__in=user_projects)

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
        environment = Environment.objects.get(api_key=env_key)
        return Identity.objects.filter(environment=environment)

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


class Identify(GenericAPIView):
    """
    Identify an identity.
    """
    serializer_class = IdentitySerializer
    # Endpoint is unauthenticated but need to override authentication classes to avoid csrf errors
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AllowAny,)

    schema = AutoSchema(
        manual_fields=[
            coreapi.Field("X-Environment-Key", location="header",
                          description="API Key for an Environment"),
            coreapi.Field("environment", required=False, location="body")
        ]
    )

    def post(self, request, *args, **kwargs):
        if 'HTTP_X_ENVIRONMENT_KEY' not in request.META:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        if 'identifier' not in request.data:
            error = {"detail": "Identifier not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        environment = get_object_or_404(Environment, api_key=request.META['HTTP_X_ENVIRONMENT_KEY'])

        identifier = request.data["identifier"]

        if Identity.objects.filter(identifier=identifier, environment=environment).count() > 0:
            error = {"detail": "Identity with that identifier already exists for this environment"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "environment": environment.id,
            "identifier": identifier
        }

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

