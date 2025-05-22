from django.urls import include, path, re_path
from rest_framework_nested import routers  # type: ignore[import-untyped]

from edge_api.identities.views import (
    EdgeIdentityFeatureStateViewSet,
    EdgeIdentityViewSet,
    EdgeIdentityWithIdentifierFeatureStateView,
    get_edge_identity_overrides,
)
from features.views import (
    EnvironmentFeatureStateViewSet,
    IdentityFeatureStateViewSet,
    create_segment_override,
)
from integrations.amplitude.views import AmplitudeConfigurationViewSet
from integrations.dynatrace.views import DynatraceConfigurationViewSet
from integrations.grafana.views import GrafanaProjectConfigurationViewSet
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
from .identities.views import IdentityViewSet
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
    r"integrations/dynatrace",
    DynatraceConfigurationViewSet,
    basename="integrations-dynatrace",
)
environments_router.register(
    r"integrations/grafana",
    GrafanaProjectConfigurationViewSet,
    basename="integrations-grafana",
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
)
edge_identity_router = routers.NestedSimpleRouter(
    environments_router,
    r"edge-identities",
    lookup="edge_identity",
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
    re_path(r"^", include(router.urls)),
    re_path(r"^", include(environments_router.urls)),
    re_path(r"^", include(identity_router.urls)),
    re_path(r"^", include(edge_identity_router.urls)),
    path(
        "environments/<str:environment_api_key>/edge-identities-featurestates",
        EdgeIdentityWithIdentifierFeatureStateView.as_view(),
        name="edge-identities-with-identifier-featurestates",
    ),
    path(
        "<str:environment_api_key>/features/<int:feature_pk>/create-segment-override/",
        create_segment_override,
        name="create-segment-override",
    ),
    path(
        "<str:environment_api_key>/edge-identity-overrides",
        get_edge_identity_overrides,
        name="edge-identity-overrides",
    ),
]
