from django.db.models import Model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet


class BaseMetricsViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    model_class: type[Model] | None = None
    lookup_url_kwarg: str | None = None

    def get_object(self):
        obj_pk = self.kwargs.get(self.lookup_url_kwarg)
        obj = get_object_or_404(self.model_class, api_key=obj_pk)

        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request, *args, **kwargs):
        obj = self.get_object()
        data = self.get_metrics(obj)
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
