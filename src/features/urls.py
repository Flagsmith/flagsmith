from django.conf.urls import url, include
from django.urls import path
from rest_framework_nested import routers

from features.views import FeatureSegmentViewSet
from features.feature_states.views import FeatureStateCreateViewSet

router = routers.DefaultRouter()
router.register(r'featurestates', FeatureStateCreateViewSet, basename='featurestates')
router.register(r'feature-segments', FeatureSegmentViewSet, basename='feature-segment')


app_name = "features"

urlpatterns = [
    path('', include(router.urls))
]
