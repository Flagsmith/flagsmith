from typing import Any

from django.conf import settings
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import routers
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from app_analytics.views import SDKAnalyticsFlags, SelfHostedTelemetryAPIView
from environments.identities.traits.views import SDKTraits
from environments.identities.views import SDKIdentities
from environments.sdk.views import SDKEnvironmentAPIView
from features.feature_health.views import feature_health_webhook
from features.views import SDKFeatureStates, get_multivariate_options
from integrations.github.views import github_webhook
from organisations.views import chargebee_webhook

traits_router = routers.DefaultRouter()
traits_router.register(r"", SDKTraits, basename="sdk-traits")

app_name = "v1"


class DocsView(APIView):  # pragma: no cover
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        # Maintain backwards-compat with /docs/?format=openapi returning raw schema
        if request.GET.get("format") == "openapi":
            return SpectacularAPIView.as_view()(request, *args, **kwargs)
        return SpectacularSwaggerView.as_view(url_name="api-v1:schema")(
            request, *args, **kwargs
        )


def swagger_schema_view(
    request: Any, *args: Any, **kwargs: Any
) -> Any:  # pragma: no cover
    # Normalize format to remove leading dot so both .json and json work
    fmt = kwargs.get("format")
    if isinstance(fmt, str) and fmt.startswith("."):
        kwargs["format"] = fmt[1:]
    return SpectacularAPIView.as_view()(request, *args, **kwargs)


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
    # Keep old name for tests expecting reverse("api-v1:schema-json", ...)
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$", swagger_schema_view, name="schema-json"
    ),
    # New endpoints
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", DocsView.as_view(), name="schema-swagger-ui"),
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
