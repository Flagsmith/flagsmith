from django.contrib.contenttypes.models import ContentType
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .models import MetadataModelField
from .serializers import MetaDataModelFieldSerializer


class MetaDataViewMixin:
    app_label = None
    model_name = None

    def get_base_metadata_fields_queryset(self):
        return MetadataModelField.objects.filter(
            field__organisation__in=self.request.user.organisations.all(),
        )

    @swagger_auto_schema(method="GET", responses={200: MetaDataModelFieldSerializer()})
    @action(
        detail=False,
        methods=["GET"],
        url_path="metadata-fields",
        serializer_class=MetaDataModelFieldSerializer,
    )
    def get_model_metadata_fields(self, request):
        content_type = ContentType.objects.get(
            app_label=self.app_label, model=self.model_name
        )

        queryset = self.get_base_metadata_fields_queryset()
        metadata_fields = queryset.filter(content_type=content_type)

        serializer = MetaDataModelFieldSerializer(metadata_fields, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method="POST",
        responses={201: MetaDataModelFieldSerializer()},
        request_body=MetaDataModelFieldSerializer(),
    )
    @action(detail=False, methods=["POST"], url_path="metadata-field")
    def create_model_metadata_field(self, request):
        serializer = MetaDataModelFieldSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not self.request.user.organisations.filter(
            id=serializer.validated_data["field"].organisation_id
        ).exists():
            raise PermissionDenied("field does not belong to the organisation")

        content_type = ContentType.objects.get(
            app_label=self.app_label, model=self.model_name
        )
        serializer.save(content_type=content_type)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method="PUT",
        responses={200: MetaDataModelFieldSerializer()},
        request_body=MetaDataModelFieldSerializer(),
    )
    @action(
        detail=False,
        methods=["PUT"],
        url_path=r"metadata-field/(?P<metadata_pk>\d+)",
    )
    def update_model_metadata_field(self, request, metadata_pk=None):
        queryset = self.get_base_metadata_fields_queryset()
        model_metadata_field = get_object_or_404(queryset, pk=metadata_pk)

        serializer = MetaDataModelFieldSerializer(
            model_metadata_field, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data)

    @update_model_metadata_field.mapping.delete
    def delete_model_metadata_field(self, request, metadata_pk):
        queryset = self.get_base_metadata_fields_queryset()

        model_metadata_field = get_object_or_404(queryset, pk=metadata_pk)

        model_metadata_field.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
