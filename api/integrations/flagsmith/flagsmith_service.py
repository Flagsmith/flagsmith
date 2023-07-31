import json
import os

import requests
from django.conf import settings

from integrations.flagsmith.exceptions import FlagsmithIntegrationError

ENVIRONMENT_JSON_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data/environment.json"
)


def update_environment_json(
    environment_key: str = None,
    api_url: str = None,
) -> None:
    environment_key = environment_key or settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY
    api_url = api_url or settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL

    response = requests.get(
        f"{api_url}/environment-document",
        headers={"X-Environment-Key": environment_key},
    )
    if response.status_code != 200:
        raise FlagsmithIntegrationError(
            f"Couldn't get defaults from Flagsmith. Got {response.status_code} response."
        )

    with open(ENVIRONMENT_JSON_PATH, "w+") as defaults:
        defaults.write(json.dumps(dict(sorted(response.json().items()))))
