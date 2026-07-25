from rest_framework_nested import routers  # type: ignore[import-untyped]

from experimentation.views import ExperimentMetricViewSet, ExperimentViewSet

app_name = "experiments"

router = routers.DefaultRouter()
router.register(r"", ExperimentViewSet, basename="experiments")

experiments_router = routers.NestedSimpleRouter(router, r"", lookup="experiment")
experiments_router.register(
    r"metrics", ExperimentMetricViewSet, basename="experiment-metrics"
)

urlpatterns = router.urls + experiments_router.urls
