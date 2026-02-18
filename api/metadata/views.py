from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from projects.models import Project
from projects.permissions import VIEW_PROJECT, NestedProjectPermissions

from .models import (
    SUPPORTED_REQUIREMENTS_MAPPING,
    MetadataField,
    MetadataModelField,
)
from .permissions import (
    MetadataFieldPermissions,
    MetadataModelFieldPermissions,
)
from .serializers import (
    ContentTypeSerializer,
    MetadataFieldQuerySerializer,
    MetadataFieldSerializer,
    MetadataModelFieldQuerySerializer,
    MetaDataModelFieldSerializer,
    ProjectMetadataFieldQuerySerializer,
    SupportedRequiredForModelQuerySerializer,
)


@method_decorator(
    name="list",
    decorator=extend_schema(parameters=[MetadataFieldQuerySerializer]),
)
class MetadataFieldViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = [MetadataFieldPermissions]
    serializer_class = MetadataFieldSerializer

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return MetadataField.objects.none()

        queryset = MetadataField.objects.filter(organisation__users=self.request.user)
        if self.action == "list":
            serializer = MetadataFieldQuerySerializer(data=self.request.query_params)
            serializer.is_valid(raise_exception=True)
            organisation_id = serializer.validated_data["organisation"]

            queryset = queryset.filter(
                organisation_id=organisation_id,
                project__isnull=True,
            )

        return queryset.prefetch_related("metadatamodelfield_set__is_required_for")


class MetaDataModelFieldViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    permission_classes = [MetadataModelFieldPermissions]
    serializer_class = MetaDataModelFieldSerializer

    def get_queryset(self):  # type: ignore[no-untyped-def]
        queryset = MetadataModelField.objects.filter(
            field__organisation_id=self.kwargs.get("organisation_pk")
        )
        serializer = MetadataModelFieldQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        content_type = serializer.validated_data.get("content_type")

        if content_type:
            queryset = queryset.filter(content_type__id=content_type)

        return queryset

    @extend_schema(responses={200: ContentTypeSerializer(many=True)})
    @action(
        detail=False,
        methods=["GET"],
        url_path="supported-content-types",
    )
    def supported_content_types(self, request, organisation_pk=None):  # type: ignore[no-untyped-def]
        need_content_type_of = list(
            chain.from_iterable(
                (key, *value) for key, value in SUPPORTED_REQUIREMENTS_MAPPING.items()
            )
        )

        qs = ContentType.objects.filter(model__in=need_content_type_of)
        serializer = ContentTypeSerializer(qs, many=True)

        return Response(serializer.data)

    @extend_schema(
        responses={200: ContentTypeSerializer(many=True)},
        parameters=[SupportedRequiredForModelQuerySerializer],
    )
    @action(
        detail=False,
        methods=["GET"],
        url_path="supported-required-for-models",
    )
    def supported_required_for_models(self, request, organisation_pk=None):  # type: ignore[no-untyped-def]
        serializer = SupportedRequiredForModelQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        supported_models = SUPPORTED_REQUIREMENTS_MAPPING.get(
            serializer.data["model_name"], []
        )
        if not supported_models:
            return Response(
                {"message": "No supported models found for the given model name."},
                status=status.HTTP_404_NOT_FOUND,
            )

        qs = ContentType.objects.filter(model__in=supported_models)
        serializer = ContentTypeSerializer(qs, many=True)  # type: ignore[assignment]

        return Response(serializer.data)


@method_decorator(
    name="list",
    decorator=extend_schema(parameters=[ProjectMetadataFieldQuerySerializer]),
)
class ProjectMetadataFieldViewSet(viewsets.ReadOnlyModelViewSet):  # type: ignore[type-arg]
    serializer_class = MetadataFieldSerializer
    permission_classes = [NestedProjectPermissions]

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return MetadataField.objects.none()

        project = get_object_or_404(
            self.request.user.get_permitted_projects(VIEW_PROJECT),
            pk=self.kwargs["project_pk"],
        )

        queryset = MetadataField.objects.filter(
            organisation=project.organisation,
            project_id=project.id,
        )

        serializer = ProjectMetadataFieldQuerySerializer(
            data=self.request.query_params
        )
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("include_organisation"):
            overridden_names = queryset.values_list("name", flat=True)
            org_fields = MetadataField.objects.filter(
                organisation=project.organisation,
                project__isnull=True,
            ).exclude(name__in=overridden_names)
            queryset = queryset | org_fields

        return queryset.prefetch_related("metadatamodelfield_set__is_required_for")
