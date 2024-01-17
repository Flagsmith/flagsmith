from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from environments.models import Environment
from features.import_export.models import FeatureExport
from projects.models import Project
from projects.permissions import VIEW_PROJECT


class FeatureImportPermissions(IsAuthenticated):
    def has_permission(
        self, request: Request, view: "WrappedAPIView"  # noqa: F821
    ) -> bool:
        if not super().has_permission(request, view):
            return False

        environment = Environment.objects.select_related(
            "project__organisation",
        ).get(id=view.kwargs["environment_id"])
        organisation = environment.project.organisation

        # Since feature imports can be destructive, use org admin.
        return request.user.is_organisation_admin(organisation)


class CreateFeatureExportPermissions(IsAuthenticated):
    def has_permission(
        self, request: Request, view: "WrappedAPIView"  # noqa: F821
    ) -> bool:
        if not super().has_permission(request, view):
            return False

        environment = Environment.objects.get(id=request.data["environment_id"])
        return request.user.is_environment_admin(environment)


class DownloadFeatureExportPermissions(IsAuthenticated):
    def has_permission(
        self, request: Request, view: "WrappedAPIView"  # noqa: F821
    ) -> bool:
        if not super().has_permission(request, view):
            return False

        feature_export = FeatureExport.objects.get(id=view.kwargs["feature_export_id"])

        return request.user.is_environment_admin(feature_export.environment)


class FeatureExportListPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ListAPIView) -> bool:
        if not super().has_permission(request, view):
            return False

        project = Project.objects.get(id=view.kwargs["project_pk"])
        # The user will only see environment feature exports
        # that the user is an environment admin.
        return request.user.has_project_permission(VIEW_PROJECT, project)


class FeatureImportListPermissions(IsAuthenticated):
    def has_permission(self, request: Request, view: ListAPIView) -> bool:
        if not super().has_permission(request, view):
            return False

        project = Project.objects.get(id=view.kwargs["project_pk"])
        # The user will only see environment feature imports
        # that the user is an environment admin.
        return request.user.has_project_permission(VIEW_PROJECT, project)
