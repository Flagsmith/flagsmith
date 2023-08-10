import json
import os

import requests
from django.conf import settings

from integrations.flagsmith.exceptions import FlagsmithIntegrationError

ENVIRONMENT_JSON_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "data/environment.json"
)

KEEP_ENVIRONMENT_FIELDS = (
    "name",
    "feature_states",
    "use_identity_composite_key_for_hashing",
)
KEEP_PROJECT_FIELDS = ("name", "organisation", "hide_disabled_flags")
KEEP_ORGANISATION_FIELDS = (
    "name",
    "feature_analytics",
    "stop_serving_flags",
    "persist_trait_data",
)


def update_environment_json(environment_key: str = None, api_url: str = None) -> None:
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

    environment_json = _get_masked_environment_data(response.json())
    with open(ENVIRONMENT_JSON_PATH, "w+") as defaults:
        defaults.write(json.dumps(environment_json, indent=2, sort_keys=True))


def _get_masked_environment_data(environment_document: dict) -> dict:
    """
    Return a cut down / masked version of the environment
    document which can be committed to VCS.
    """

    project_json = environment_document.pop("project")
    organisation_json = project_json.pop("organisation")

    return {
        "id": 0,
        "api_key": "masked",
        **{
            k: v
            for k, v in environment_document.items()
            if k in KEEP_ENVIRONMENT_FIELDS
        },
        "project": {
            "id": 0,
            **{k: v for k, v in project_json.items() if k in KEEP_PROJECT_FIELDS},
            "organisation": {
                "id": 0,
                **{
                    k: v
                    for k, v in organisation_json.items()
                    if k in KEEP_ORGANISATION_FIELDS
                },
            },
            "segments": [],
        },
    }
