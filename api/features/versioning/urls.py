from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedSimpleRouter

from features.versioning.views import (
    EnvironmentFeatureVersionFeatureStatesViewSet,
    EnvironmentFeatureVersionViewSet,
)

app_name = "versioning"

ef_version_router = DefaultRouter()
ef_version_router.register(
    "versions",
    EnvironmentFeatureVersionViewSet,
    basename="environment-feature-versions",
)

ef_version_fs_router = NestedSimpleRouter(
    ef_version_router, "versions", lookup="environment_feature_version"
)
ef_version_fs_router.register(
    "featurestates",
    EnvironmentFeatureVersionFeatureStatesViewSet,
    basename="environment-feature-version-featurestates",
)

urlpatterns = [
    path(
        "environments/<int:environment_pk>/features/<int:feature_pk>/",
        include(ef_version_router.urls),
    ),
    path(
        "environments/<int:environment_pk>/features/<int:feature_pk>/",
        include(ef_version_fs_router.urls),
    ),
]
