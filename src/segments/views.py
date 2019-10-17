import logging

from django.core.exceptions import ObjectDoesNotExist
from django.utils.decorators import method_decorator
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from environments.exceptions import EnvironmentHeaderNotPresentError
from environments.models import Environment, Identity
from segments.serializers import SegmentSerializer
from util.views import SDKAPIView
from . import serializers

logger = logging.getLogger()
logger.setLevel(logging.INFO)


@method_decorator(name='list', decorator=swagger_auto_schema(
    manual_parameters=[
        openapi.Parameter('identity', openapi.IN_QUERY,
                          'Optionally provide the id of an identity to get only the segments they match',
                          required=False, type=openapi.TYPE_INTEGER)
    ]
))
class SegmentViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SegmentSerializer

    def get_queryset(self):
        project = get_object_or_404(self.request.user.get_permitted_projects(), pk=self.kwargs['project_pk'])
        queryset = project.segments.all()

        identity_pk = self.request.query_params.get('identity')
        if identity_pk:
            identity = Identity.objects.get(pk=identity_pk)
            queryset = queryset.filter(id__in=[segment.id for segment in identity.get_segments()])

        return queryset

    def create(self, request, *args, **kwargs):
        project_pk = request.data.get('project')
        if int(project_pk) not in [project.id for project in self.request.user.get_permitted_projects()]:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)


class SDKSegments(SDKAPIView):
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
