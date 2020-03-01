from django.conf.urls import url, include
from rest_framework_nested import routers

from features.views import FeatureStateViewSet
from .views import IdentityViewSet, EnvironmentViewSet, TraitViewSet, WebhookViewSet, UserEnvironmentPermissionsViewSet, \
    UserPermissionGroupEnvironmentPermissionsViewSet

router = routers.DefaultRouter()
router.register(r'', EnvironmentViewSet, basename="environment")

environments_router = routers.NestedSimpleRouter(router, r'', lookup="environment")
environments_router.register(r'identities', IdentityViewSet, basename="environment-identities")
environments_router.register(r'webhooks', WebhookViewSet, basename='environment-webhooks')
environments_router.register(r'featurestates', FeatureStateViewSet, basename="environment-featurestates")
environments_router.register(r'user-permissions', UserEnvironmentPermissionsViewSet,
                             basename='environment-user-permissions')
environments_router.register(r'user-group-permissions', UserPermissionGroupEnvironmentPermissionsViewSet,
                             basename='environment-user-group-permissions')

identity_router = routers.NestedSimpleRouter(environments_router, r'identities', lookup="identity")
identity_router.register(r'featurestates', FeatureStateViewSet, basename="identity-featurestates")
identity_router.register(r'traits', TraitViewSet, basename="identities-traits")

app_name = "environments"

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(environments_router.urls)),
    url(r'^', include(identity_router.urls))
]
