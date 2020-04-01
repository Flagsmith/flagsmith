from django.conf.urls import url, include
from rest_framework_nested import routers

from features.views import FeatureStateCreateViewSet

router = routers.DefaultRouter()
router.register(r'', FeatureStateCreateViewSet, basename="featurestates")


app_name = "features"

urlpatterns = [
    url(r'^featurestates', include(router.urls))
]
