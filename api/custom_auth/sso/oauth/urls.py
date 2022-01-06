from django.urls import path

from custom_auth.sso.oauth.views import login_with_github, login_with_google

app_name = "oauth"

urlpatterns = [
    path("google/", login_with_google, name="google-oauth-login"),
    path("github/", login_with_github, name="github-oauth-login"),
]
