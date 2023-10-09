from app_analytics.views import SDKAnalyticsFlags, SelfHostedTelemetryAPIView
from django.urls import include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import authentication, permissions, routers

from environments.identities.traits.views import SDKTraits
from environments.identities.views import SDKIdentities
from environments.sdk.views import SDKEnvironmentAPIView
from features.views import SDKFeatureStates
from organisations.views import chargebee_webhook

schema_view = get_schema_view(
    openapi.Info(
        title="Flagsmith API",
        default_version="v1",
        description="",
        license=openapi.License(name="BSD License"),
        contact=openapi.Contact(email="support@flagsmith.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    authentication_classes=[authentication.SessionAuthentication],
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
    # Client SDK urls
    re_path(r"^flags/$", SDKFeatureStates.as_view(), name="flags"),
    re_path(r"^identities/$", SDKIdentities.as_view(), name="sdk-identities"),
    re_path(r"^traits/", include(traits_router.urls), name="traits"),
    re_path(r"^analytics/flags/$", SDKAnalyticsFlags.as_view()),
    re_path(r"^analytics/telemetry/$", SelfHostedTelemetryAPIView.as_view()),
    re_path(
        r"^environment-document/$",
        SDKEnvironmentAPIView.as_view(),
        name="environment-document",
    ),
    # API documentation
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^docs/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
