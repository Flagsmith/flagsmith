from common.core.utils import is_oss
from django.urls import path

from onboarding.views import (
    receive_support_request_from_self_hosted_view,
    send_onboarding_request_to_saas_flagsmith_view,
)

urlpatterns = [
    path(
        "onboarding/request/receive/",
        receive_support_request_from_self_hosted_view,
        name="receive-onboarding-request",
    ),
]
if is_oss:
    urlpatterns.append(
        path(
            "onboarding/request/send/",
            send_onboarding_request_to_saas_flagsmith_view,
            name="send-onboarding-request",
        ),
    )
