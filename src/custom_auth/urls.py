from django.urls import include, path

from custom_auth.views import CustomAuthTokenLoginOrRequestMFACode

app_name = "custom_auth"


urlpatterns = [
    # Override auth/login endpoint for throttling login requests
    path(
        "login/",
        CustomAuthTokenLoginOrRequestMFACode.as_view(),
        name="custom-mfa-authtoken-login",
    ),
    path("", include("djoser.urls")),
    path("", include("trench.urls")),  # MFA
    path("", include("trench.urls.djoser")),  # override necessary urls for MFA auth
    path("oauth/", include("custom_auth.oauth.urls")),
]
