# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from projects.serializers import ProjectSerializer
from organisations.serializers import OrganisationSerializer
from users.serializers import UserFullSerializer, InviteSerializer


class OrganisationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganisationSerializer

    def get_queryset(self):
        if self.request.user.organisations:
            return self.request.user.organisations.all()
        else:
            return []

    def create(self, request):
        """
        Override create method to add new organisation to authenticated user
        """
        user = request.user
        serializer = OrganisationSerializer(data=request.data)
        if serializer.is_valid():
            org = serializer.save()
            user.organisations.add(org)
            user.save()

            return Response(serializer.data, status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @detail_route()
    def projects(self, request, pk):
        organisation = self.get_object()
        projects = organisation.projects.all()
        return Response(ProjectSerializer(projects, many=True).data)

    @detail_route()
    def users(self, request, pk):
        organisation = self.get_object()
        users = organisation.users.all()
        return Response(UserFullSerializer(users, many=True).data)

    @detail_route(methods=["POST"])
    def invite(self, request, pk):
        organisation = self.get_object()

        if "emails" not in request.data:
            raise ValidationError({"detail": "List of emails must be provided"})

        if "frontend_base_url" not in request.data:
            raise ValidationError({"detail": "Must provide base url"})

        invites = []

        for email in request.data["emails"]:
            invites.append({"email": email, "frontend_base_url": request.data["frontend_base_url"],
                            "organisation": organisation.id, "invited_by": self.request.user.id})

        invites_serializer = InviteSerializer(data=invites, many=True)

        if invites_serializer.is_valid():
            invites_serializer.save()
        else:
            raise ValidationError(invites_serializer.errors)

        return Response(status=status.HTTP_201_CREATED)
