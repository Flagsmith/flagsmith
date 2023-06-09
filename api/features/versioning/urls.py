from django.urls import include, path
from rest_framework.routers import DefaultRouter

from features.versioning.views import EnvironmentFeatureVersionViewSet

router = DefaultRouter()
router.register("versions", EnvironmentFeatureVersionViewSet, basename="versions")

urlpatterns = [
    path(
        "environments/<int:environment_pk>/features/<int:feature_pk>/",
        include(router.urls),
    )
]
