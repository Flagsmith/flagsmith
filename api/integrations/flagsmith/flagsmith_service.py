import json
import os
from copy import deepcopy

import deepdiff
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

    new_environment_document = get_masked_environment_data(response.json())
    with open(ENVIRONMENT_JSON_PATH, "w+") as defaults:
        current_environment_document = defaults.read() or "{}"

    if deepdiff.DeepDiff(
        json.loads(current_environment_document),
        new_environment_document,
        exclude_regex_paths=[
            r"root\['feature_states'\]\[\d+\]\['django_id'\]",
            r"root\['feature_states'\]\[\d+\]\['featurestate_uuid'\]",
        ],
    ):
        defaults.write(json.dumps(new_environment_document, indent=2, sort_keys=True))


def get_masked_environment_data(environment_document: dict) -> dict:
    """
    Return a cut down / masked version of the environment
    document which can be committed to VCS.
    """

    _copy = deepcopy(environment_document)

    project_json = _copy.pop("project")
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
