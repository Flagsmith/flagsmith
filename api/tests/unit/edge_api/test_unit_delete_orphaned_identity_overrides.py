import uuid

import pytest
from django.core.management import CommandError, call_command
from mypy_boto3_dynamodb.service_resource import Table
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from environments.dynamodb import (
    DynamoEnvironmentV2Wrapper,
    DynamoIdentityWrapper,
)
from environments.dynamodb.types import IdentityOverrideV2
from environments.dynamodb.utils import (
    get_environments_v2_identity_override_document_key,
)
from environments.models import Environment
from features.models import Feature, FeatureState
from projects.models import Project
from util.engine_models.identities.models import IdentityModel
from util.mappers import (
    map_engine_identity_to_identity_document,
    map_feature_state_to_engine,
    map_identity_override_to_identity_override_document,
)

COMMAND = "delete_orphaned_identity_overrides"


def _put_identity_override(
    table: Table,
    environment: Environment,
    feature: Feature,
    identifier: str,
    identity_uuid: str,
) -> str:
    document = map_identity_override_to_identity_override_document(
        IdentityOverrideV2(
            environment_id=str(environment.id),
            environment_api_key=environment.api_key,
            document_key=get_environments_v2_identity_override_document_key(
                feature_id=feature.id,
                identity_uuid=identity_uuid,
            ),
            identifier=identifier,
            identity_uuid=identity_uuid,
            feature_state=map_feature_state_to_engine(
                FeatureState(
                    feature=feature,
                    enabled=True,
                    environment=environment,
                ),
            ),
        )
    )
    table.put_item(Item=document)
    return document["document_key"]  # type: ignore[return-value]


def _put_identity(
    table: Table,
    environment: Environment,
    feature: Feature | None,
    identifier: str,
    identity_uuid: str,
) -> None:
    identity = IdentityModel(
        identifier=identifier,
        environment_api_key=environment.api_key,
        identity_uuid=identity_uuid,  # type: ignore[arg-type]
    )
    if feature:
        identity.identity_features.append(
            map_feature_state_to_engine(
                FeatureState(
                    feature=feature,
                    enabled=True,
                    environment=environment,
                ),
            )
        )
    table.put_item(Item=map_engine_identity_to_identity_document(identity))


def _get_document_keys(table: Table, environment: Environment) -> set[str]:
    return {
        str(item["document_key"])
        for item in table.scan()["Items"]
        if str(item["environment_id"]) == str(environment.id)
    }


@pytest.fixture()
def orphaned_overrides(
    flagsmith_environments_v2_table: Table,
    flagsmith_identities_table: Table,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    dynamo_enabled_project: Project,
    environment: Environment,
    feature: Feature,
) -> dict[str, str]:
    """
    Four identity overrides: one still valid, and one for each way of going stale.
    """
    document_keys = {}

    valid_uuid = str(uuid.uuid4())
    document_keys["valid"] = _put_identity_override(
        flagsmith_environments_v2_table, environment, feature, "valid", valid_uuid
    )
    _put_identity(flagsmith_identities_table, environment, feature, "valid", valid_uuid)

    # The identity was deleted, so no document exists for the identifier.
    document_keys["identity_deleted"] = _put_identity_override(
        flagsmith_environments_v2_table,
        environment,
        feature,
        "identity-deleted",
        str(uuid.uuid4()),
    )

    # The identifier was recreated, so it resolves to a different identity.
    document_keys["identity_uuid_changed"] = _put_identity_override(
        flagsmith_environments_v2_table,
        environment,
        feature,
        "uuid-changed",
        str(uuid.uuid4()),
    )
    _put_identity(
        flagsmith_identities_table,
        environment,
        feature,
        "uuid-changed",
        str(uuid.uuid4()),
    )

    # The same identity no longer overrides the feature.
    override_removed_uuid = str(uuid.uuid4())
    document_keys["override_removed"] = _put_identity_override(
        flagsmith_environments_v2_table,
        environment,
        feature,
        "override-removed",
        override_removed_uuid,
    )
    _put_identity(
        flagsmith_identities_table,
        environment,
        None,
        "override-removed",
        override_removed_uuid,
    )

    return document_keys


def test_delete_orphaned_identity_overrides__stale_overrides__deletes_only_stale(
    flagsmith_environments_v2_table: Table,
    environment: Environment,
    orphaned_overrides: dict[str, str],
) -> None:
    # Given
    assert len(_get_document_keys(flagsmith_environments_v2_table, environment)) == 4

    # When
    call_command(COMMAND, environment_id=environment.id)

    # Then
    assert _get_document_keys(flagsmith_environments_v2_table, environment) == {
        orphaned_overrides["valid"]
    }


def test_delete_orphaned_identity_overrides__dry_run__deletes_nothing(
    flagsmith_environments_v2_table: Table,
    environment: Environment,
    orphaned_overrides: dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given / When
    call_command(COMMAND, environment_id=environment.id, dry_run=True)

    # Then
    assert _get_document_keys(flagsmith_environments_v2_table, environment) == set(
        orphaned_overrides.values()
    )
    reported = capsys.readouterr().out
    assert "identity_deleted" in reported
    assert "identity_uuid_changed" in reported
    assert "override_removed" in reported
    assert orphaned_overrides["valid"] not in reported


def test_delete_orphaned_identity_overrides__override_recreated__leaves_it_alone(
    flagsmith_environments_v2_table: Table,
    environment: Environment,
    orphaned_overrides: dict[str, str],
    mocker: MockerFixture,
    log: StructuredLogCapture,
) -> None:
    # Given - every delete loses the condition, as it would if the override had
    # been recreated between being read and being deleted
    mocker.patch(
        "edge_api.management.commands.delete_orphaned_identity_overrides"
        ".delete_orphaned_identity_override",
        return_value=False,
    )

    # When
    call_command(COMMAND, environment_id=environment.id)

    # Then
    assert _get_document_keys(flagsmith_environments_v2_table, environment) == set(
        orphaned_overrides.values()
    )
    assert log.has("identity_override.delete_skipped", level="info")
    assert log.events[-1] == {
        "level": "info",
        "event": "identity_override.reconciliation_finished",
        "environment__id": environment.id,
        "dry_run": False,
        "orphaned__count": 3,
        "deleted__count": 0,
        "skipped__count": 3,
        "reasons": {
            "identity_deleted": 1,
            "identity_uuid_changed": 1,
            "override_removed": 1,
        },
    }


def test_delete_orphaned_identity_overrides__no_such_environment__raises_expected(
    db: None,
) -> None:
    # Given
    environment_id = 99999

    # When / Then
    with pytest.raises(
        CommandError, match=f"Environment {environment_id} does not exist"
    ):
        call_command(COMMAND, environment_id=environment_id)


def test_delete_orphaned_identity_overrides__override_rewritten__skips_deletion(
    flagsmith_environments_v2_table: Table,
    flagsmith_identities_table: Table,
    dynamodb_wrapper_v2: DynamoEnvironmentV2Wrapper,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
    dynamo_enabled_project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    """
    An override recreated between being read and being deleted must survive —
    otherwise the repair carries the same race as the bug it repairs.
    """
    # Given
    identity_uuid = str(uuid.uuid4())
    document_key = _put_identity_override(
        flagsmith_environments_v2_table,
        environment,
        feature,
        "rewritten",
        identity_uuid,
    )

    # When - the document is rewritten against a different identity, so the
    # delete's condition no longer holds
    flagsmith_environments_v2_table.update_item(
        Key={"environment_id": str(environment.id), "document_key": document_key},
        UpdateExpression="SET identity_uuid = :uuid",
        ExpressionAttributeValues={":uuid": str(uuid.uuid4())},
    )
    deleted = dynamodb_wrapper_v2.delete_identity_override_if_unchanged(
        environment_id=environment.id,
        document_key=document_key,
        identity_uuid=identity_uuid,
    )

    # Then
    assert deleted is False
    assert _get_document_keys(flagsmith_environments_v2_table, environment) == {
        document_key
    }
