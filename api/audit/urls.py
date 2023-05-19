from django.conf.urls import include, url
from rest_framework import routers

from audit.views import AllAuditLogViewSet

router = routers.DefaultRouter()
router.register(r"", AllAuditLogViewSet, basename="audit")


urlpatterns = [url(r"^", include(router.urls))]
