# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from features.models import Feature, FeatureState, FLAG
from features.serializers import FeatureSerializer
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

    @detail_route()
    def environments(self, request, pk):
        project = self.get_object()
        environments = project.environments.all()
        return Response(EnvironmentSerializerLight(environments, many=True).data)

    @detail_route(methods=["GET", "POST", "PUT", "DELETE"])
    def features(self, request, pk):
        project = self.get_object()

        self.queryset = Feature.objects.filter(project=project)
        self.serializer_class = FeatureSerializer

        if request.method == "POST":
            data = {
                "project": project.id,
                "name": request.data["name"],
                "initial_value": request.data.get("initial_value"),
                "description": request.data.get("description"),
                "type": request.data.get("type", FLAG),
                "default_enabled": request.data.get("default_enabled", False),
            }

            f_serializer = FeatureSerializer(data=data)

            if f_serializer.is_valid():
                f_serializer.save()
                return Response(f_serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(f_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "PUT":
            data = {
                "id": request.data["id"],
                "project": project.id,
                "name": request.data["name"],
                "initial_value": request.data["initial_value"]
            }

            serializer = FeatureSerializer(data=data)

            if serializer.is_valid():
                feature_to_update = Feature.objects.get(pk=data["id"])
                feature_updated = serializer.update(feature_to_update, serializer.validated_data)
                return Response(FeatureSerializer(feature_updated).data,
                                status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == "DELETE":
            Feature.objects.get(pk=request.data["id"]).delete()
            return Response(status=status.HTTP_200_OK)

        else:
            serializer = FeatureSerializer(instance=self.queryset, many=True)
            return Response(serializer.data)
