from django.urls import path

from custom_auth.oauth.slack import SlackAuthView
from custom_auth.oauth.views import login_with_github, login_with_google

app_name = "oauth"

urlpatterns = [
    path("google/", login_with_google, name="google-oauth-login"),
    path("github/", login_with_github, name="github-oauth-login"),
    path("slack/", SlackAuthView.as_view(), name="slack-oauth-login"),
]
