from flag_engine.environments.models import EnvironmentModel

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from util.pydantic import exclude_model_fields

SDKEnvironmentDocumentModel = exclude_model_fields(
    EnvironmentModel,
    *IDENTITY_INTEGRATIONS_RELATION_NAMES,
    "dynatrace_config",
)
