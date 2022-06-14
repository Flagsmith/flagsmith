from django.conf.urls import include, url
from django.urls import path
from rest_framework_nested import routers

from features.multivariate.views import MultivariateFeatureOptionViewSet
from features.views import FeatureViewSet
from integrations.datadog.views import DataDogConfigurationViewSet
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

nested_features_router = routers.NestedSimpleRouter(
    projects_router, r"features", lookup="feature"
)
nested_features_router.register(
    r"mv-options", MultivariateFeatureOptionViewSet, basename="feature-mv-options"
)

app_name = "projects"

urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^", include(projects_router.urls)),
    url(r"^", include(nested_features_router.urls)),
    path(
        "<int:project_pk>/all-user-permissions/<int:user_pk>/",
        get_user_project_permissions,
        name="all-user-permissions",
    ),
]
