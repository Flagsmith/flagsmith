# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from analytics.query import get_events_for_organisation
from organisations.models import OrganisationRole
from organisations.permissions import OrganisationPermission, NestedOrganisationEntityPermission
from organisations.serializers import OrganisationSerializerFull, MultiInvitesSerializer
from projects.serializers import ProjectSerializer
from users.models import Invite
from users.serializers import InviteSerializer, InviteListSerializer, UserIdSerializer


class OrganisationViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, OrganisationPermission)

    def get_serializer_class(self):
        if self.action == 'remove_users':
            return UserIdSerializer
        elif self.action == 'invite':
            return MultiInvitesSerializer
        return OrganisationSerializerFull

    def get_serializer_context(self):
        context = super(OrganisationViewSet, self).get_serializer_context()
        if self.action in ('remove_users', 'invite'):
            context['organisation'] = self.kwargs.get('pk')
        return context

    def get_queryset(self):
        return self.request.user.organisations.all()

    def create(self, request, **kwargs):
        """
        Override create method to add new organisation to authenticated user
        """
        user = request.user
        serializer = OrganisationSerializerFull(data=request.data)
        if serializer.is_valid():
            org = serializer.save()
            user.add_organisation(org, OrganisationRole.ADMIN)

            return Response(serializer.data, status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def projects(self, request, pk):
        organisation = self.get_object()
        projects = organisation.projects.all()
        return Response(ProjectSerializer(projects, many=True).data)

    @action(detail=True, methods=["POST"])
    def invite(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

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
    permission_classes = (IsAuthenticated, NestedOrganisationEntityPermission)

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
