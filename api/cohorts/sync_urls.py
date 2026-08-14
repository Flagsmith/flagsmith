from rest_framework.routers import DefaultRouter

from cohorts.sync_views import AmplitudeCohortSyncViewSet

app_name = "cohort-sync"

router = DefaultRouter()
router.register(r"amplitude/lists", AmplitudeCohortSyncViewSet, basename="amplitude")

urlpatterns = router.urls
