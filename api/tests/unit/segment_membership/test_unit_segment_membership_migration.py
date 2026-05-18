import importlib
from unittest.mock import MagicMock

from clickhouse_connect.driver import Client
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

# Migration module names start with a digit, which `import` can't parse;
# `importlib.import_module` is the only way in.
migration_module = importlib.import_module(
    "segment_membership.migrations.0002_setup_clickhouse_identities_schema"
)


def test_setup_clickhouse_identities_schema__unconfigured__skips(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given ClickHouse settings unconfigured
    settings.CLICKHOUSE_ENABLED = False
    open_client = mocker.patch.object(migration_module, "open_clickhouse_client")

    # When the migration's RunPython entry runs
    migration_module.setup_clickhouse_identities_schema(MagicMock(), MagicMock())

    # Then it short-circuits without opening a client
    open_client.assert_not_called()


def test_setup_clickhouse_identities_schema__configured__runs_ddl(
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given ClickHouse configured and a mocked client
    settings.CLICKHOUSE_ENABLED = True
    client = MagicMock(spec=Client)
    open_client = mocker.patch.object(migration_module, "open_clickhouse_client")
    open_client.return_value.__enter__.return_value = client

    # When the migration's RunPython entry runs
    migration_module.setup_clickhouse_identities_schema(MagicMock(), MagicMock())

    # Then the migration's DDL was executed against the client. The PoC's
    # schema overrides the engine's default with ReplacingMergeTree + an
    # inserted_at version column; assert on the full DDL string the
    # migration owns rather than peeking inside it.
    client.command.assert_called_once_with(migration_module._SCHEMA_DDL)
