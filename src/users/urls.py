from django.conf import settings
from django.conf.urls import url, include
from rest_framework import routers

from .views import FFAdminUserViewSet, AdminInitView

app_name = "users"
router = routers.DefaultRouter()
router.register(r'', FFAdminUserViewSet, base_name="user")

urlpatterns = [
    url(r'^', include(router.urls)),
]
if settings.ALLOW_ADMIN_INITIATION_VIA_URL:
    urlpatterns.insert(0, url(r'init/', AdminInitView.as_view()))
