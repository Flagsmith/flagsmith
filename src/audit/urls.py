from django.conf.urls import url, include
from rest_framework import routers

from audit.views import AuditLogViewSet

router = routers.DefaultRouter()
router.register(r'', AuditLogViewSet, base_name='audit')


urlpatterns = [
    url(r'^', include(router.urls))
]