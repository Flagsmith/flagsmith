import logging
from typing import Generator, Iterable

from flag_engine.identities.models import IdentityModel

from environments.dynamodb import (
    DynamoEnvironmentV2Wrapper,
    DynamoIdentityWrapper,
)
from environments.dynamodb.types import (
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.models import Environment
from util.mappers import map_engine_feature_state_to_identity_override

logger = logging.getLogger(__name__)


def migrate_environments_to_v2(project_id: int) -> IdentityOverridesV2Changeset | None:
    dynamo_wrapper_v2 = DynamoEnvironmentV2Wrapper()
    identity_wrapper = DynamoIdentityWrapper()

    if not (dynamo_wrapper_v2.is_enabled and identity_wrapper.is_enabled):
        return None

    logger.info("Migrating environments to v2 for project %d", project_id)

    environments_to_migrate = Environment.objects.filter(project_id=project_id)
    identity_overrides_to_migrate = _iter_paginated_overrides(
        identity_wrapper=identity_wrapper,
        environments=environments_to_migrate,
    )

    changeset = IdentityOverridesV2Changeset(
        to_put=list(identity_overrides_to_migrate), to_delete=[]
    )
    logger.info(
        "Retrieved %d identity overrides to migrate for project %d",
        len(changeset.to_put),
        project_id,
    )

    dynamo_wrapper_v2.write_environments(environments_to_migrate)
    dynamo_wrapper_v2.update_identity_overrides(changeset)

    logger.info("Finished migrating environments to v2 for project %d", project_id)
    return changeset


def _iter_paginated_overrides(
    *,
    identity_wrapper: DynamoIdentityWrapper,
    environments: Iterable[Environment],
) -> Generator[IdentityOverrideV2, None, None]:
    for environment in environments:
        environment_api_key = environment.api_key
        for item in identity_wrapper.iter_all_items_paginated(
            environment_api_key=environment_api_key,
        ):
            identity = IdentityModel.parse_obj(item)
            for feature_state in identity.identity_features:
                yield map_engine_feature_state_to_identity_override(
                    feature_state=feature_state,
                    identity_uuid=str(identity.identity_uuid),
                    identifier=identity.identifier,
                    environment_api_key=environment_api_key,
                    environment_id=str(environment.id),
                )
