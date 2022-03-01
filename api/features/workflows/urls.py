from django.urls import include, path
from rest_framework import routers

from features.workflows.views import ChangeRequestViewSet

router = routers.DefaultRouter()
router.register("change-requests", ChangeRequestViewSet, basename="change-requests")

app_name = "workflows"

urlpatterns = [path("", include(router.urls))]
