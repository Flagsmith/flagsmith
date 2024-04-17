from copy import deepcopy
from functools import lru_cache

import jsonref
from drf_yasg.openapi import Schema
from flag_engine.environments.models import EnvironmentModel

SKIP_PROPERTIES = [
    "amplitude_config",
    "dynatrace_config",
    "heap_config",
    "mixpanel_config",
    "rudderstack_config",
    "segment_config",
    "webhook_config",
]
SKIP_DEFINITIONS = ["IntegrationModel", "WebhookModel"]


@lru_cache()
def get_environment_document_response() -> Schema:
    model_json_schema = EnvironmentModel.model_json_schema(mode="serialization")

    # Restrict segment rule recursion to two levels.
    segment_rule_schema = deepcopy(model_json_schema["$defs"]["SegmentRuleModel"])
    del segment_rule_schema["properties"]["rules"]
    model_json_schema["$defs"]["SegmentRuleInnerModel"] = segment_rule_schema
    model_json_schema["$defs"]["SegmentRuleModel"]["properties"]["rules"]["items"][
        "$ref"
    ] = "#/$defs/SegmentRuleInnerModel"

    # Remove integrations.
    for prop in SKIP_PROPERTIES:
        del model_json_schema["properties"][prop]
    for definition in SKIP_DEFINITIONS:
        del model_json_schema["$defs"][definition]

    return Schema(**jsonref.replace_refs(model_json_schema))
