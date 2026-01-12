from django.conf import settings
from django.urls import include, path, re_path
from drf_spectacular.views import (
    SpectacularJSONAPIView,
    SpectacularYAMLAPIView,
)
from rest_framework import permissions, routers

from api.views import SpectacularElementsView
from app_analytics.views import SDKAnalyticsFlags, SelfHostedTelemetryAPIView
from environments.identities.traits.views import SDKTraits
from environments.identities.views import SDKIdentities
from environments.sdk.views import SDKEnvironmentAPIView
from features.feature_health.views import feature_health_webhook
from features.views import SDKFeatureStates, get_multivariate_options
from integrations.github.views import github_webhook
from organisations.views import chargebee_webhook

schema_view_permission_class = (  # pragma: no cover
    permissions.IsAuthenticated
    if settings.REQUIRE_AUTHENTICATION_FOR_API_DOCS
    else permissions.AllowAny
)

traits_router = routers.DefaultRouter()
traits_router.register(r"", SDKTraits, basename="sdk-traits")

app_name = "v1"

urlpatterns = [
    re_path(r"^organisations/", include("organisations.urls"), name="organisations"),
    re_path(r"^projects/", include("projects.urls"), name="projects"),
    re_path(r"^environments/", include("environments.urls"), name="environments"),
    re_path(r"^features/", include("features.urls"), name="features"),
    re_path(
        r"^multivariate/", include("features.multivariate.urls"), name="multivariate"
    ),
    re_path(r"^segments/", include("segments.urls"), name="segments"),
    re_path(r"^users/", include("users.urls")),
    re_path(r"^e2etests/", include("e2etests.urls")),
    re_path(r"^audit/", include("audit.urls")),
    re_path(r"^auth/", include("custom_auth.urls")),
    re_path(r"^metadata/", include("metadata.urls")),
    # Chargebee webhooks
    re_path(r"cb-webhook/", chargebee_webhook, name="chargebee-webhook"),
    # GitHub integration webhook
    re_path(r"github-webhook/", github_webhook, name="github-webhook"),
    re_path(r"cb-webhook/", chargebee_webhook, name="chargebee-webhook"),
    # Feature health webhook
    re_path(
        r"feature-health/(?P<path>.{0,100})$",
        feature_health_webhook,
        name="feature-health-webhook",
    ),
    re_path(r"^onboarding/", include("onboarding.urls", namespace="onboarding")),
    # Client SDK urls
    re_path(r"^flags/$", SDKFeatureStates.as_view(), name="flags"),
    re_path(
        r"^flags/(?P<feature_id>[0-9]+)/multivariate-options/$",
        get_multivariate_options,
        name="get-multivariate-options",
    ),
    re_path(r"^identities/$", SDKIdentities.as_view(), name="sdk-identities"),
    re_path(r"^traits/", include(traits_router.urls), name="traits"),
    re_path(r"^analytics/flags/$", SDKAnalyticsFlags.as_view(), name="analytics-flags"),
    re_path(r"^analytics/telemetry/$", SelfHostedTelemetryAPIView.as_view()),
    re_path(
        r"^environment-document/$",
        SDKEnvironmentAPIView.as_view(),
        name="environment-document",
    ),
    re_path("", include("features.versioning.urls", namespace="versioning")),
    # API documentation
    path(
        "swagger.json",
        SpectacularJSONAPIView.as_view(
            permission_classes=[schema_view_permission_class],
        ),
        name="schema-json",
    ),
    path(
        "swagger.yaml",
        SpectacularYAMLAPIView.as_view(
            permission_classes=[schema_view_permission_class],
        ),
        name="schema-yaml",
    ),
    path(
        "docs/",
        SpectacularElementsView.as_view(
            url_name="v1:schema-json",
            permission_classes=[schema_view_permission_class],
        ),
        name="schema-swagger-ui",
    ),
    # Test webhook url
    re_path(r"^webhooks/", include("webhooks.urls", namespace="webhooks")),
    path("", include("projects.code_references.urls", namespace="code_references")),
]

if settings.SPLIT_TESTING_INSTALLED:
    from split_testing.views import (  # type: ignore[import-not-found]
        ConversionEventTypeView,
        CreateConversionEventView,
        SplitTestViewSet,
    )

    split_testing_router = routers.DefaultRouter()
    split_testing_router.register(r"", SplitTestViewSet, basename="split-tests")

    urlpatterns += [
        re_path(
            r"^split-testing/", include(split_testing_router.urls), name="split-testing"
        ),
        re_path(
            r"^split-testing/conversion-events/",
            CreateConversionEventView.as_view(),
            name="conversion-events",
        ),
        path(
            "conversion-event-types/",
            ConversionEventTypeView.as_view(),
            name="conversion-event-types",
        ),
    ]
