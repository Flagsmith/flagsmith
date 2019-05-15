import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from environments.exceptions import EnvironmentHeaderNotPresentError
from environments.models import Environment
from projects.models import Project
from segments.serializers import SegmentSerializer
from . import serializers

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SegmentSerializer

    def get_queryset(self):
        project = Project.objects.get(pk=self.kwargs['project_pk'])
        return project.segments.all()


class SDKSegments(GenericAPIView):
    serializer_class = SegmentSerializer
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            environment = Environment.get_environment_from_request(request)
        except EnvironmentHeaderNotPresentError:
            error = {"detail": "Environment Key header not provided"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            error_response = {"error": "Environment not found for provided key"}
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(environment.project.segments.all(), many=True).data,
                        status=status.HTTP_200_OK)
