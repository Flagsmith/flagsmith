from django.conf.urls import include, url
from rest_framework import routers

from audit.views import AuditLogViewSet

router = routers.DefaultRouter()
router.register(r"", AuditLogViewSet, basename="audit")


urlpatterns = [url(r"^", include(router.urls))]
