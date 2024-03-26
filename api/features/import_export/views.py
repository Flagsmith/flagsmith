import json

from django.conf import settings
from django.db.models import QuerySet
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from environments.models import Environment

from .models import (
    FeatureExport,
    FeatureImport,
    FlagsmithOnFlagsmithFeatureExport,
)
from .permissions import (
    CreateFeatureExportPermissions,
    DownloadFeatureExportPermissions,
    FeatureExportListPermissions,
    FeatureImportListPermissions,
    FeatureImportPermissions,
)
from .serializers import (
    CreateFeatureExportSerializer,
    FeatureExportSerializer,
    FeatureImportSerializer,
    FeatureImportUploadSerializer,
)


@swagger_auto_schema(
    method="POST",
    request_body=CreateFeatureExportSerializer(),
    responses={201: FeatureExportSerializer()},
)
@api_view(["POST"])
@permission_classes([CreateFeatureExportPermissions])
def create_feature_export(request: Request) -> Response:
    serializer = CreateFeatureExportSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    feature_export = serializer.save()
    response_serializer = FeatureExportSerializer(feature_export)

    return Response(response_serializer.data, status=201)


@swagger_auto_schema(
    method="POST",
    request_body=FeatureImportUploadSerializer(),
    responses={201: FeatureImportSerializer()},
)
@api_view(["POST"])
@permission_classes([FeatureImportPermissions])
def feature_import(request: Request, environment_id: int) -> Response:
    upload_serializer = FeatureImportUploadSerializer(data=request.data)
    upload_serializer.is_valid(raise_exception=True)
    _feature_import = upload_serializer.save(environment_id=environment_id)
    serializer = FeatureImportSerializer(instance=_feature_import)
    return Response(serializer.data, status=201)


@swagger_auto_schema(
    method="GET",
    responses={200: "File downloaded"},
    operation_description="This endpoint is to download a feature export file from a specific environment",
)
@api_view(["GET"])
@permission_classes([DownloadFeatureExportPermissions])
def download_feature_export(request: Request, feature_export_id: int) -> Response:
    feature_export = get_object_or_404(FeatureExport, id=feature_export_id)

    response = Response(
        json.loads(feature_export.data), content_type="application/json"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=feature_export.{feature_export_id}.json"
    )
    return response


@swagger_auto_schema(
    method="GET",
    responses={200: "Flagsmith on Flagsmith File downloaded"},
    operation_description="This endpoint is to download an feature export to enable flagsmith on flagsmith",
)
@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def download_flagsmith_on_flagsmith(request: Request) -> Response:
    if (
        not settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_ENVIRONMENT_ID
        or not settings.FLAGSMITH_ON_FLAGSMITH_FEATURE_EXPORT_TAG_ID
    ):
        # No explicit settings on both feature settings, so 404.
        raise Http404("This system is not configured for this download.")

    fof = FlagsmithOnFlagsmithFeatureExport.objects.order_by("-created_at").first()

    if fof is None:
        raise Http404("There is no present downloadable export.")

    response = Response(
        json.loads(fof.feature_export.data), content_type="application/json"
    )
    response.headers["Content-Disposition"] = (
        f"attachment; filename=flagsmith_on_flagsmith.{fof.id}.json"
    )
    return response


class FeatureExportListView(ListAPIView):
    serializer_class = FeatureExportSerializer
    permission_classes = [FeatureExportListPermissions]

    def get_queryset(self) -> QuerySet[FeatureExport]:
        environment_ids = []
        user = self.request.user

        for environment in Environment.objects.filter(
            project_id=self.kwargs["project_pk"],
        ):
            if user.is_environment_admin(environment):
                environment_ids.append(environment.id)

        return FeatureExport.objects.filter(environment__in=environment_ids).order_by(
            "-created_at"
        )


class FeatureImportListView(ListAPIView):
    serializer_class = FeatureImportSerializer
    permission_classes = [FeatureImportListPermissions]

    def get_queryset(self) -> QuerySet[FeatureImport]:
        environment_ids = []
        user = self.request.user

        for environment in Environment.objects.filter(
            project_id=self.kwargs["project_pk"],
        ):
            if user.is_environment_admin(environment):
                environment_ids.append(environment.id)

        return FeatureImport.objects.filter(environment__in=environment_ids).order_by(
            "-created_at"
        )
