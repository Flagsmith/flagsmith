from django.conf.urls import url, include
from rest_framework_nested import routers

from features.views import FeatureStateViewSet
from .views import IdentityViewSet, EnvironmentViewSet, TraitViewSet

router = routers.DefaultRouter()
router.register(r'', EnvironmentViewSet, base_name="environment")

environments_router = routers.NestedSimpleRouter(router, r'', lookup="environment")
environments_router.register(r'identities', IdentityViewSet, base_name="environment-identities")

identity_router = routers.NestedSimpleRouter(environments_router, r'identities', lookup="identity")
identity_router.register(r'featurestates', FeatureStateViewSet, base_name="identity-featurestates")
identity_router.register(r'traits', TraitViewSet, base_name="identities-traits")
environments_router.register(r'featurestates', FeatureStateViewSet, base_name="environment-featurestates")


app_name = "environments"

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(environments_router.urls)),
    url(r'^', include(identity_router.urls))
]
