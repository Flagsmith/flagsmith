from django.urls import include, re_path
from rest_framework import routers

from audit.views import AllAuditLogViewSet

router = routers.DefaultRouter()
router.register(r"", AllAuditLogViewSet, basename="audit")


urlpatterns = [re_path(r"^", include(router.urls))]
