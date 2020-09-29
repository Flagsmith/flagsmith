from django.conf.urls import url, include
from rest_framework import routers

from .views import DataDogConfigurationViewSet

router = routers.DefaultRouter()
router.register(r'datadog', DataDogConfigurationViewSet, basename='datadog')

urlpatterns = [
    url(r'^', include(router.urls))
]