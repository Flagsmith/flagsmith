from django.conf.urls import include
from django.urls import path
from rest_framework_nested import routers

from .views import MetadataFieldViewSet

router = routers.DefaultRouter()

router.register(r"fields", MetadataFieldViewSet, basename="metadata-fields")


app_name = "metadata"

urlpatterns = [
    path("", include(router.urls)),
]
