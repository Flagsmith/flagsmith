from django.conf.urls import include, url
from rest_framework_nested import routers

from edge_api.identities.views import EdgeIdentityFeatureStateViewSet
from features.views import (
    EnvironmentFeatureStateViewSet,
    IdentityFeatureStateViewSet,
)
from integrations.amplitude.views import AmplitudeConfigurationViewSet
from integrations.heap.views import HeapConfigurationViewSet
from integrations.mixpanel.views import MixpanelConfigurationViewSet
from integrations.rudderstack.views import RudderstackConfigurationViewSet
from integrations.segment.views import SegmentConfigurationViewSet
from integrations.slack.views import (
    SlackEnvironmentViewSet,
    SlackGetChannelsViewSet,
)
from integrations.webhook.views import WebhookConfigurationViewSet

from .identities.traits.views import TraitViewSet
from .identities.views import EdgeIdentityViewSet, IdentityViewSet
from .permissions.views import (
    UserEnvironmentPermissionsViewSet,
    UserPermissionGroupEnvironmentPermissionsViewSet,
)
from .views import EnvironmentAPIKeyViewSet, EnvironmentViewSet, WebhookViewSet

router = routers.DefaultRouter()
router.register(r"", EnvironmentViewSet, basename="environment")

environments_router = routers.NestedSimpleRouter(router, r"", lookup="environment")
environments_router.register(
    r"identities", IdentityViewSet, basename="environment-identities"
)
environments_router.register(
    r"edge-identities", EdgeIdentityViewSet, basename="environment-edge-identities"
)
environments_router.register(
    r"webhooks", WebhookViewSet, basename="environment-webhooks"
)
environments_router.register(
    r"featurestates",
    EnvironmentFeatureStateViewSet,
    basename="environment-featurestates",
)
environments_router.register(
    r"user-permissions",
    UserEnvironmentPermissionsViewSet,
    basename="environment-user-permissions",
)
environments_router.register(
    r"user-group-permissions",
    UserPermissionGroupEnvironmentPermissionsViewSet,
    basename="environment-user-group-permissions",
)
environments_router.register(
    r"integrations/amplitude",
    AmplitudeConfigurationViewSet,
    basename="integrations-amplitude",
)
environments_router.register(
    r"integrations/segment",
    SegmentConfigurationViewSet,
    basename="integrations-segment",
)
environments_router.register(
    r"integrations/heap",
    HeapConfigurationViewSet,
    basename="integrations-heap",
)
environments_router.register(
    r"integrations/mixpanel",
    MixpanelConfigurationViewSet,
    basename="integrations-mixpanel",
)
environments_router.register(
    r"integrations/slack", SlackEnvironmentViewSet, basename="integrations-slack"
)

environments_router.register(
    r"integrations/webhook",
    WebhookConfigurationViewSet,
    basename="integrations-webhook",

edge_identity_router = routers.NestedSimpleRouter(
    environments_router, r"edge-identities", lookup="edge_identity"
)
edge_identity_router.register(
    r"edge-featurestates",
    EdgeIdentityFeatureStateViewSet,
    basename="edge-identity-featurestates",
)
environments_router.register(
    r"integrations/slack-channels",
    SlackGetChannelsViewSet,
    basename="integrations-slack-channels",
)
environments_router.register(
    r"integrations/rudderstack",
    RudderstackConfigurationViewSet,
    basename="integrations-rudderstack",
)
identity_router = routers.NestedSimpleRouter(
    environments_router, r"identities", lookup="identity"
)
identity_router.register(
    r"featurestates", IdentityFeatureStateViewSet, basename="identity-featurestates"
)

identity_router.register(r"traits", TraitViewSet, basename="identities-traits")

environments_router.register(r"api-keys", EnvironmentAPIKeyViewSet, basename="api-keys")

app_name = "environments"

urlpatterns = [
    url(r"^", include(router.urls)),
    url(r"^", include(environments_router.urls)),
    url(r"^", include(identity_router.urls)),
    url(r"^", include(edge_identity_router.urls)),
]
