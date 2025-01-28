import importlib

from django.conf import settings
from django.urls import include, path, re_path
from rest_framework_nested import routers

from audit.views import ProjectAuditLogViewSet
from features.feature_external_resources.views import (
    FeatureExternalResourceViewSet,
)
from features.feature_health.views import FeatureHealthProviderViewSet
from features.import_export.views import (
    FeatureExportListView,
    FeatureImportListView,
)
from features.multivariate.views import MultivariateFeatureOptionViewSet
from features.views import FeatureViewSet
from integrations.datadog.views import DataDogConfigurationViewSet
from integrations.grafana.views import GrafanaProjectConfigurationViewSet
from integrations.launch_darkly.views import LaunchDarklyImportRequestViewSet
from integrations.new_relic.views import NewRelicConfigurationViewSet
from projects.tags.views import TagViewSet
from segments.views import SegmentViewSet

from . import views
from .views import (
    UserPermissionGroupProjectPermissionsViewSet,
    UserProjectPermissionsViewSet,
    get_user_project_permissions,
)

router = routers.DefaultRouter()
router.register(r"", views.ProjectViewSet, basename="project")

projects_router = routers.NestedSimpleRouter(router, r"", lookup="project")
projects_router.register(r"features", FeatureViewSet, basename="project-features")
projects_router.register(r"segments", SegmentViewSet, basename="project-segments")
projects_router.register(
    r"user-permissions",
    UserProjectPermissionsViewSet,
    basename="project-user-permissions",
)
projects_router.register(
    r"user-group-permissions",
    UserPermissionGroupProjectPermissionsViewSet,
    basename="project-user-group-permissions",
)
projects_router.register(r"tags", TagViewSet, basename="tags")
projects_router.register(
    r"integrations/datadog",
    DataDogConfigurationViewSet,
    basename="integrations-datadog",
)
projects_router.register(
    r"integrations/new-relic",
    NewRelicConfigurationViewSet,
    basename="integrations-new-relic",
)
projects_router.register(
    r"imports/launch-darkly",
    LaunchDarklyImportRequestViewSet,
    basename="imports-launch-darkly",
)
projects_router.register(
    r"integrations/grafana",
    GrafanaProjectConfigurationViewSet,
    basename="integrations-grafana",
)
projects_router.register(
    "audit",
    ProjectAuditLogViewSet,
    basename="project-audit",
)
projects_router.register(
    "feature-health-providers",
    FeatureHealthProviderViewSet,
    basename="feature-health-providers",
)

if settings.WORKFLOWS_LOGIC_INSTALLED:  # pragma: no cover
    workflow_views = importlib.import_module("workflows_logic.views")
    projects_router.register(
        r"change-requests",
        workflow_views.ProjectChangeRequestViewSet,
        basename="project-change-requests",
    )


nested_features_router = routers.NestedSimpleRouter(
    projects_router, r"features", lookup="feature"
)
nested_features_router.register(
    r"mv-options", MultivariateFeatureOptionViewSet, basename="feature-mv-options"
)

nested_features_router.register(
    r"feature-external-resources",
    FeatureExternalResourceViewSet,
    basename="feature-external-resources",
)

app_name = "projects"

urlpatterns = [
    re_path(r"^", include(router.urls)),
    re_path(r"^", include(projects_router.urls)),
    re_path(r"^", include(nested_features_router.urls)),
    path(
        "<int:project_pk>/all-user-permissions/<int:user_pk>/",
        get_user_project_permissions,
        name="all-user-permissions",
    ),
    path(
        "<int:project_pk>/feature-exports/",
        FeatureExportListView.as_view(),
        name="feature-exports",
    ),
    path(
        "<int:project_pk>/feature-imports/",
        FeatureImportListView.as_view(),
        name="feature-imports",
    ),
]
