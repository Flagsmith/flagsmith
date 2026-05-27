from rest_framework.routers import DefaultRouter

from experimentation.views import ExperimentViewSet

app_name = "experiments"

router = DefaultRouter()
router.register(r"", ExperimentViewSet, basename="experiments")

urlpatterns = router.urls
