from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from projects.permissions import VIEW_PROJECT

from . import serializers
from .models import Tag
from .permissions import TagPermissions


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.TagSerializer
    permission_classes = [IsAuthenticated, TagPermissions]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Tag.objects.none()

        project = get_object_or_404(
            self.request.user.get_permitted_projects(VIEW_PROJECT),
            pk=self.kwargs["project_pk"],
        )
        queryset = project.tags.all()

        return queryset

    def perform_create(self, serializer):
        project_id = int(self.kwargs["project_pk"])
        serializer.save(project_id=project_id)

    def perform_update(self, serializer):
        project_id = int(self.kwargs["project_pk"])
        serializer.save(project_id=project_id)

    def destroy(self, request: Request, *args, **kwargs):
        instance = self.get_object()

        if instance.is_system_tag:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Cannot delete a system tag."},
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        url_path=r"get-by-uuid/(?P<uuid>[0-9a-f-]+)",
        methods=["get"],
    )
    def get_by_uuid(self, request: Request, project_pk: int, uuid: str):
        qs = self.get_queryset()
        tag = get_object_or_404(qs, uuid=uuid)
        serializer = self.get_serializer(tag)
        return Response(serializer.data)
