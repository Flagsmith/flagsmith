from django.conf.urls import include, url
from django.urls import path
from rest_framework_nested import routers

from features.views import FeatureSegmentViewSet, FeatureStateCreateViewSet

router = routers.DefaultRouter()
router.register(r"featurestates", FeatureStateCreateViewSet, basename="featurestates")
router.register(r"feature-segments", FeatureSegmentViewSet, basename="feature-segment")


app_name = "features"

urlpatterns = [path("", include(router.urls))]
