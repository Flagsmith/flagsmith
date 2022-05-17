from django.urls import include, path
from rest_framework.routers import DefaultRouter

from custom_auth.views import (
    CustomAuthTokenLoginOrRequestMFACode,
    CustomAuthTokenLoginWithMFACode,
    ThrottledUserViewSet,
)

app_name = "custom_auth"

throttled_user_router = DefaultRouter()
throttled_user_router.register(r"users", ThrottledUserViewSet)
urlpatterns = [
    # Override some endpoints for throttling requests
    path(
        "login/",
        CustomAuthTokenLoginOrRequestMFACode.as_view(),
        name="custom-mfa-authtoken-login",
    ),
    path(
        "login/code/",
        CustomAuthTokenLoginWithMFACode.as_view(),
        name="mfa-authtoken-login-code",
    ),
    path("", include(throttled_user_router.urls)),
    # NOTE: endpoints provided by `djoser.urls`
    # are deprecated and will be removed in the next Major release
    path("", include("djoser.urls")),
    path("", include("trench.urls")),  # MFA
    path("", include("trench.urls.djoser")),  # override necessary urls for MFA auth
    path("oauth/", include("custom_auth.oauth.urls")),
]
