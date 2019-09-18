# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from analytics.query import get_events_for_organisation
from organisations.serializers import OrganisationSerializer
from projects.serializers import ProjectSerializer
from users.models import Invite
from users.serializers import InviteSerializer, UserListSerializer, InviteListSerializer, UserIdSerializer


class OrganisationViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        if self.action == 'remove_users':
            return UserIdSerializer
        return OrganisationSerializer

    def get_serializer_context(self):
        context = super(OrganisationViewSet, self).get_serializer_context()
        if self.action == 'remove_users':
            context['organisation'] = self.kwargs.get('pk')
        return context

    def get_queryset(self):
        return self.request.user.organisations.all()

    def create(self, request, **kwargs):
        """
        Override create method to add new organisation to authenticated user
        """
        user = request.user
        serializer = OrganisationSerializer(data=request.data)
        if serializer.is_valid():
            org = serializer.save()
            user.add_organisation(org)

            return Response(serializer.data, status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def projects(self, request, pk):
        organisation = self.get_object()
        projects = organisation.projects.all()
        return Response(ProjectSerializer(projects, many=True).data)

    @action(detail=True)
    def users(self, request, pk):
        organisation = self.get_object()
        users = organisation.users.all()
        return Response(UserListSerializer(users, many=True).data)

    @action(detail=True, methods=["POST"])
    def invite(self, request, pk):
        organisation = self.get_object()

        if "emails" not in request.data:
            raise ValidationError({"detail": "List of emails must be provided"})

        if "frontend_base_url" not in request.data:
            raise ValidationError({"detail": "Must provide base url"})

        invites = []

        for email in request.data["emails"]:
            invite = Invite.objects.filter(email=email, organisation=organisation)
            if invite.exists():
                data = {"error": "Invite already exists for this email address."}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            invites.append({"email": email, "frontend_base_url": request.data["frontend_base_url"],
                            "organisation": organisation.id, "invited_by": self.request.user.id})

        invites_serializer = InviteSerializer(data=invites, many=True)

        if invites_serializer.is_valid():
            invite = invites_serializer.save()
            return Response(InviteListSerializer(instance=invite, many=True).data, status=status.HTTP_201_CREATED)
        else:
            raise ValidationError(invites_serializer.errors)

    @action(detail=True, methods=['POST'], url_path='remove-users')
    def remove_users(self, request, pk):
        """
        Takes a list of users and removes them from the organisation provided in the url
        """
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=200)

    @action(detail=True, methods=["GET"])
    def usage(self, request, pk):
        organisation = self.get_object()

        try:
            events = get_events_for_organisation(organisation)
        except (TypeError, ValueError):
            # TypeError can be thrown when getting service account if not configured
            # ValueError can be thrown if GA returns a value that cannot be converted to integer
            return Response({"error": "Couldn't get number of events for organisation."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"events": events}, status=status.HTTP_200_OK)


class InviteViewSet(viewsets.ModelViewSet):
    serializer_class = InviteListSerializer

    def get_queryset(self):
        organisation_pk = self.kwargs.get('organisation_pk')
        if int(organisation_pk) not in [org.id for org in self.request.user.organisations.all()]:
            return []
        return Invite.objects.filter(organisation__id=organisation_pk)

    @action(detail=True, methods=["POST"])
    def resend(self, request, organisation_pk, pk):
        invite = self.get_object()
        invite.send_invite_mail()
        return Response(status=status.HTTP_200_OK)
