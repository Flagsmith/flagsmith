import requests
from task_processor.decorators import register_task_handler

SEND_SUPPORT_REQUEST_URL = (
    "https://api.flagsmith.com/api/v1/onboarding/request/receive/"
)


@register_task_handler()
def send_onboarding_request_to_saas_flagsmith(
    first_name: str, last_name: str, email: str, organisation_name: str
) -> None:
    data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "organisation_name": organisation_name,
    }
    response = requests.post(SEND_SUPPORT_REQUEST_URL, data=data, timeout=30)
    response.raise_for_status()
