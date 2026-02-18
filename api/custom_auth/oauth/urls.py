from django.urls import path
from rest_framework.routers import DefaultRouter

from custom_auth.oauth.views import (
    OIDCConfigurationViewSet,
    login_with_github,
    login_with_google,
    oidc_authorize,
    oidc_callback,
)

app_name = "oauth"

router = DefaultRouter()
router.register(r"oidc/configuration", OIDCConfigurationViewSet, basename="oidc-configuration")

urlpatterns = [
    path("google/", login_with_google, name="google-oauth-login"),
    path("github/", login_with_github, name="github-oauth-login"),
    path("oidc/<slug:name>/authorize/", oidc_authorize, name="oidc-authorize"),
    path("oidc/<slug:name>/callback/", oidc_callback, name="oidc-callback"),
    *router.urls,
]
