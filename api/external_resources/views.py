from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ExternalResources, FeatureExternalResources
from .serializers import (
    ExternalResourcesSerializer,
    FeatureExternalResourcesSerializer,
)


class ExternalResourcesViewSet(viewsets.ModelViewSet):
    serializer_class = ExternalResourcesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        print("DEBUG: self:", self.kwargs)
        return ExternalResources.objects.filter(id=self.kwargs["pk"])

    def perform_update(self, serializer):
        external_resource_id = int(self.kwargs["id"])
        serializer.save(id=external_resource_id)

    @action(
        detail=False,
        methods=["GET"],
        url_path="external-resource-by-project/(?P<project_pk>[^/.]+)",
    )
    def external_resource_list(self, request, project_pk, *args, **kwargs):
        external_resources = ExternalResources.objects.filter(project_id=project_pk)
        serializer = ExternalResourcesSerializer(external_resources, many=True)
        return Response(serializer.data)


class FeatureExternalResourcesViewSet(viewsets.ModelViewSet):
    serializer_class = FeatureExternalResourcesSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FeatureExternalResources.objects.filter(
            external_resource=self.kwargs["external_resource_pk"]
        )

    def perform_update(self, serializer):
        external_resource = ExternalResources.objects.get(
            pk=int(self.kwargs["external_resource_pk"])
        )
        serializer.save(external_resource=external_resource)

    def perform_create(self, serializer):
        external_resource = ExternalResources.objects.get(
            pk=int(self.kwargs["external_resource_pk"])
        )
        serializer.save(external_resource=external_resource)


# class RolesByUserViewSet(
#     mixins.ListModelMixin, mixins.DestroyModelMixin, GenericViewSet
# ):
#     serializer_class = ExternalResourcesSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         feature_pk = self.kwargs["feature_pk"]
#         return ExternalResources.objects.filter(feature_external_resource__pk=feature_pk)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         user_pk = self.kwargs["user_pk"]
#         user_role_instances = FeatureExternalResources.objects.filter(external_resources=instance, user=user_pk)
#         user_role_instances.delete()

#         return Response(status=status.HTTP_204_NO_CONTENT)
