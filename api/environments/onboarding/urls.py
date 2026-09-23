from django.urls import path

from environments.onboarding.views import EnvironmentOnboardingStatusAPIView

app_name = "onboarding"

urlpatterns = [
    path(
        "",
        EnvironmentOnboardingStatusAPIView.as_view(),
        name="onboarding-status",
    ),
]
