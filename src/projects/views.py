# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from environments.serializers import EnvironmentSerializerLight
from projects.models import Project
from projects.serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        user_organisations = self.request.user.organisations.all()
        user_org_ids = [org.id for org in user_organisations]
        queryset = Project.objects.filter(organisation__in=user_org_ids)

        return queryset

    @action(detail=True)
    def environments(self, request, pk):
        project = self.get_object()
        environments = project.environments.all()
        return Response(EnvironmentSerializerLight(environments,
                                                   many=True).data)
