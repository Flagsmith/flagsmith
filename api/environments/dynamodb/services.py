import logging
from decimal import Decimal
from typing import Generator, Iterable

from flag_engine.identities.models import IdentityModel

from environments.dynamodb import (
    CapacityBudgetExceeded,
    DynamoEnvironmentV2Wrapper,
    DynamoIdentityWrapper,
)
from environments.dynamodb.types import (
    EdgeV2MigrationResult,
    IdentityOverridesV2Changeset,
    IdentityOverrideV2,
)
from environments.models import Environment
from projects.models import EdgeV2MigrationStatus
from util.mappers import map_engine_feature_state_to_identity_override

logger = logging.getLogger(__name__)


def migrate_environments_to_v2(
    project_id: int,
    capacity_budget: Decimal,
) -> EdgeV2MigrationResult | None:
    """
    Migrate project's environments to `environments_v2` table.

    :param project_id: ID of project to migrate.
    :param capacity_budget: Max read capacity to spend when reading identities. Can be 0.

    :returns: `EdgeV2MigrationResult` object or `None`.

    If provided `capacity_budget` exceeded, including a budget of 0,
    `EdgeV2MigrationResult.status` is set to `INCOMPLETE` and no identity overrides get
    written to `environments_v2` table.
    """
    dynamo_wrapper_v2 = DynamoEnvironmentV2Wrapper()
    identity_wrapper = DynamoIdentityWrapper()

    if not (dynamo_wrapper_v2.is_enabled and identity_wrapper.is_enabled):
        return None

    logger.info("Migrating environments to v2 for project %d", project_id)

    environments_to_migrate = Environment.objects.filter_for_document_builder(
        project_id=project_id
    )

    identity_overrides_changeset = IdentityOverridesV2Changeset(to_put=[], to_delete=[])
    result_status = EdgeV2MigrationStatus.COMPLETE

    try:
        to_put = list(
            _iter_paginated_overrides(
                identity_wrapper=identity_wrapper,
                environments=environments_to_migrate,
                capacity_budget=capacity_budget,
            )
        )
    except CapacityBudgetExceeded as exc:
        result_status = EdgeV2MigrationStatus.INCOMPLETE
        logger.warning("Incomplete migration for project %d", project_id, exc_info=exc)
    else:
        identity_overrides_changeset.to_put = to_put
        logger.info(
            "Retrieved %d identity overrides to migrate for project %d",
            len(to_put),
            project_id,
        )

    dynamo_wrapper_v2.write_environments(environments_to_migrate)
    dynamo_wrapper_v2.update_identity_overrides(identity_overrides_changeset)

    logger.info("Finished migrating environments to v2 for project %d", project_id)
    return EdgeV2MigrationResult(
        identity_overrides_changeset=identity_overrides_changeset,
        status=result_status,
    )


def _iter_paginated_overrides(
    *,
    identity_wrapper: DynamoIdentityWrapper,
    environments: Iterable[Environment],
    capacity_budget: Decimal,
) -> Generator[IdentityOverrideV2, None, None]:
    for environment in environments:
        environment_api_key = environment.api_key
        for item in identity_wrapper.iter_all_items_paginated(
            environment_api_key=environment_api_key,
            capacity_budget=capacity_budget,
            projection_expression="environment_api_key, identifier, identity_features, identity_uuid",
            overrides_only=True,
        ):
            identity = IdentityModel.model_validate(item)
            for feature_state in identity.identity_features:
                yield map_engine_feature_state_to_identity_override(
                    feature_state=feature_state,
                    identity_uuid=str(identity.identity_uuid),
                    identifier=identity.identifier,
                    environment_api_key=environment_api_key,
                    environment_id=str(environment.id),
                )
