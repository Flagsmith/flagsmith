from common.projects.permissions import VIEW_PROJECT
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from environments.models import Environment
from features.import_export.models import FeatureExport
from projects.models import Project


class FeatureImportPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False

        environment = Environment.objects.get(id=view.kwargs["environment_id"])

        # Since feature imports can be destructive, use environment admin.
        # This mirrors the feature export permissions, and is satisfied by
        # organisation and project admins too.
        return request.user.is_environment_admin(environment)  # type: ignore[union-attr,no-any-return]


class CreateFeatureExportPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False

        environment = Environment.objects.get(id=request.data["environment_id"])
        return request.user.is_environment_admin(environment)  # type: ignore[union-attr,no-any-return]


class DownloadFeatureExportPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: APIView) -> bool:
        if not super().has_permission(request, view):
            return False

        feature_export = FeatureExport.objects.get(id=view.kwargs["feature_export_id"])

        return request.user.is_environment_admin(feature_export.environment)  # type: ignore[union-attr,no-any-return]


class FeatureExportListPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ListAPIView) -> bool:  # type: ignore[override,type-arg]
        if not super().has_permission(request, view):
            return False

        project = Project.objects.get(id=view.kwargs["project_pk"])
        # The user will only see environment feature exports
        # that the user is an environment admin.
        return request.user.has_project_permission(VIEW_PROJECT, project)  # type: ignore[union-attr,no-any-return]


class FeatureImportListPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ListAPIView) -> bool:  # type: ignore[override,type-arg]
        if not super().has_permission(request, view):
            return False

        project = Project.objects.get(id=view.kwargs["project_pk"])
        # The user will only see environment feature imports
        # that the user is an environment admin.
        return request.user.has_project_permission(VIEW_PROJECT, project)  # type: ignore[union-attr,no-any-return]
