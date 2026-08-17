from rest_framework.routers import SimpleRouter

from cohorts.sync_views import AmplitudeCohortSyncViewSet

app_name = "cohort-sync"

# SimpleRouter: nothing here is browsed by a person.
router = SimpleRouter()
router.register(r"amplitude/lists", AmplitudeCohortSyncViewSet, basename="amplitude")

urlpatterns = router.urls
