from common.core.utils import is_saas
from django.urls import path

from environments.onboarding.views import EnvironmentOnboardingStatusAPIView

app_name = "onboarding"

urlpatterns = []
if is_saas():
    urlpatterns.append(
        path(
            "",
            EnvironmentOnboardingStatusAPIView.as_view(),
            name="onboarding-status",
        )
    )
