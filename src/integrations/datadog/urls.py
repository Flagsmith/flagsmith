from django.conf.urls import url, include
from rest_framework import routers

from integrations.datadog.views import DataDogConfigurationViewSet

router = routers.DefaultRouter()
router.register(r'', DataDogConfigurationViewSet, basename='datadogconfiguration')


urlpatterns = [
    url(r'^', include(router.urls))
]