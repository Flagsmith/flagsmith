from django.conf.urls import include, url
from rest_framework_nested import routers

from features.views import FeatureViewSet
from integrations.datadog.views import DataDogConfigurationViewSet
from integrations.new_relic.views import NewRelicConfigurationViewSet
from projects.tags.views import TagViewSet
from segments.views import SegmentViewSet

from . import views
from .views import (
    UserPermissionGroupProjectPermissionsViewSet,
    UserProjectPermissionsViewSet,
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


app_name = "projects"

urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^", include(projects_router.urls)),
    url(r"^", include(nested_features_router.urls)),
]
