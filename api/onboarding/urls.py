from common.core.utils import is_oss, is_saas
from django.urls import path

from onboarding.views import (
    ReceiveSupportRequestFromSelfHosted,
    send_onboarding_request_to_saas_flagsmith_view,
)

app_name = "onboarding"
urlpatterns = []
if is_saas():
    urlpatterns.append(
        path(
            "request/receive/",
            ReceiveSupportRequestFromSelfHosted.as_view(),
            name="receive-onboarding-request",
        )
    )

if is_oss():
    urlpatterns.append(
        path(
            "request/send/",
            send_onboarding_request_to_saas_flagsmith_view,
            name="send-onboarding-request",
        ),
    )
