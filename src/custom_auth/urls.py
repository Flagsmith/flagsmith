from django.urls import include, path

from custom_auth.views import (
    CustomAuthTokenLoginOrRequestMFACode,
    CustomAuthTokenLoginWithMFACode,
)

app_name = "custom_auth"


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
    path("", include("djoser.urls")),
    path("", include("trench.urls")),  # MFA
    path("", include("trench.urls.djoser")),  # override necessary urls for MFA auth
    path("oauth/", include("custom_auth.oauth.urls")),
]
