from django.urls import path

from custom_auth.oauth.views import login_with_google, login_with_github

app_name = "oauth"

urlpatterns = [
    path("google/", login_with_google),
    path("github/", login_with_github)
]
