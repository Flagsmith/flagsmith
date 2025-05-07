from abc import abstractmethod
from typing import Any, Dict

from django.db.models import Model
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from environments.models import Environment
from metrics.types import EnvMetricsPayload


class BaseMetricsViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    model_class: type[Model] | None = None
    lookup_url_kwarg: str
    serializer_class: type[Serializer[Dict[str, Any]]] | None

    # TODO: Extend types when used for other models
    @abstractmethod
    def get_metrics(self, obj: Environment) -> EnvMetricsPayload:
        """
        Return metrics for the given object.
        Must be implemented by subclasses.
        """
        pass

    def get_object(self) -> Model:
        obj_pk = self.kwargs.get(self.lookup_url_kwarg)
        assert self.model_class is not None
        obj = get_object_or_404(self.model_class, api_key=obj_pk)

        self.check_object_permissions(self.request, obj)
        return obj

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        obj = self.get_object()
        assert isinstance(obj, Environment)
        metrics = self.get_metrics(obj)
        assert self.serializer_class is not None
        serializer = self.serializer_class(data={"metrics": metrics})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
