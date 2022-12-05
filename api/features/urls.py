from django.conf import settings
from django.conf.urls import include
from django.urls import path
from rest_framework_nested import routers

from features.feature_segments.views import FeatureSegmentViewSet
from features.views import (
    SimpleFeatureStateViewSet,
    get_feature_by_uuid,
    get_feature_state_by_uuid,
)

router = routers.DefaultRouter()
router.register(r"featurestates", SimpleFeatureStateViewSet, basename="featurestates")
router.register(r"feature-segments", FeatureSegmentViewSet, basename="feature-segment")


app_name = "features"

urlpatterns = [
    path("", include(router.urls)),
    path("get-by-uuid/<uuid:uuid>/", get_feature_by_uuid, name="get-feature-by-uuid"),
    path(
        "featurestates/get-by-uuid/<uuid:uuid>/",
        get_feature_state_by_uuid,
        name="get-feature-state-by-uuid",
    ),
]

if settings.WORKFLOWS_LOGIC_INSTALLED:
    urlpatterns.append(
        path(
            "workflows/",
            include(
                f"{settings.WORKFLOWS_LOGIC_MODULE_PATH}.urls", namespace="workflows"
            ),
        )
    )
