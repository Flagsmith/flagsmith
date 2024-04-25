from flag_engine.environments.models import EnvironmentModel

from util.pydantic import exclude_model_fields

SDKEnvironmentDocumentModel = exclude_model_fields(
    EnvironmentModel,
    "amplitude_config",
    "dynatrace_config",
    "heap_config",
    "mixpanel_config",
    "rudderstack_config",
    "segment_config",
    "webhook_config",
)
