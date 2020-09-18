import logging

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from projects.models import Project
from .models import FeatureSegment
from .permissions import FeaturePermissions
from .serializers import CreateFeatureSerializer, FeatureSerializer, \
    FeatureSegmentCreateSerializer, FeatureSegmentListSerializer, FeatureSegmentQuerySerializer, FeatureSegmentChangePrioritiesSerializer

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class FeatureViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, FeaturePermissions]

    def get_serializer_class(self):
        if self.action in ['create', 'update']:
            return CreateFeatureSerializer
        else:
            return FeatureSerializer

    def get_queryset(self):
        user_projects = self.request.user.get_permitted_projects(["VIEW_PROJECT"])
        project = get_object_or_404(user_projects, pk=self.kwargs['project_pk'])

        return project.features.all()

    def create(self, request, *args, **kwargs):
        project_id = request.data.get('project')
        project = Project.objects.get(pk=project_id)

        if project.organisation not in request.user.organisations.all():
            return Response(status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)


def organisation_has_got_feature(request, organisation):
    """
    Helper method to set flag against organisation to confirm that they've requested their
    feature states for analytics purposes

    :param request: HTTP request
    :return: True if value set. None otherwise.
    """
    if organisation.has_requested_features:
        return None

    referer = request.META.get("HTTP_REFERER")
    if not referer or "bullet-train.io" in referer:
        return None
    else:
        organisation.has_requested_features = True
        organisation.save()
        return True


@method_decorator(name='list', decorator=swagger_auto_schema(query_serializer=FeatureSegmentQuerySerializer()))
@method_decorator(
    name='update_priorities', decorator=swagger_auto_schema(responses={200: FeatureSegmentListSerializer(many=True)})
)
class FeatureSegmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    def get_queryset(self):
        permitted_projects = self.request.user.get_permitted_projects(['VIEW_PROJECT'])
        queryset = FeatureSegment.objects.filter(feature__project__in=permitted_projects)

        if self.action == 'list':
            filter_serializer = FeatureSegmentQuerySerializer(data=self.request.query_params)
            filter_serializer.is_valid(raise_exception=True)
            return queryset.filter(**filter_serializer.data)

        return queryset

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FeatureSegmentCreateSerializer

        if self.action == 'update_priorities':
            return FeatureSegmentChangePrioritiesSerializer

        return FeatureSegmentListSerializer

    def get_serializer(self, *args, **kwargs):
        if self.action == 'update_priorities':
            # update the serializer kwargs to ensure docs here are correct
            kwargs = {**kwargs, 'many': True, 'partial': True}
        return super(FeatureSegmentViewSet, self).get_serializer(*args, **kwargs)

    @action(detail=False, methods=['POST'], url_path='update-priorities')
    def update_priorities(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_instances = serializer.save()
        return Response(FeatureSegmentListSerializer(instance=updated_instances, many=True).data)
