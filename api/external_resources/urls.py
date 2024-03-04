from django.conf.urls import include, url
from rest_framework_nested import routers

from .views import ExternalResourcesViewSet

router = routers.DefaultRouter()
router.register(r"", ExternalResourcesViewSet, basename="external-resources")
external_resource_router = routers.NestedSimpleRouter(
    router, r"", lookup="external_resource"
)

urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^", include(external_resource_router.urls)),
]
