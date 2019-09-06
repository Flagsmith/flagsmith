import logging

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import viewsets, status, pagination
from rest_framework.generics import GenericAPIView, get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from environments.exceptions import EnvironmentHeaderNotPresentError
from environments.models import Environment
from segments.serializers import SegmentSerializer
from util.util import get_user_permitted_projects
from . import serializers

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SegmentSerializer

    def get_queryset(self):
        project = get_object_or_404(get_user_permitted_projects(self.request.user), pk=self.kwargs['project_pk'])
        return project.segments.all()

    def create(self, request, *args, **kwargs):
        project_pk = request.data.get('project')
        if project_pk not in [project.id for project in get_user_permitted_projects(self.request.user)]:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)


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
