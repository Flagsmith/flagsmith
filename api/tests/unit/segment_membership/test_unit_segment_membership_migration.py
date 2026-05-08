import importlib
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

migration_module = importlib.import_module(
    "segment_membership.migrations.0002_setup_snowflake_identities_schema"
)


def test_setup_snowflake_identities_schema__unconfigured__skips(
    mocker: MockerFixture,
) -> None:
    # Given Snowflake settings unconfigured
    mocker.patch.object(
        migration_module,
        "is_snowflake_configured",
        return_value=False,
    )
    open_sess = mocker.patch.object(migration_module, "open_snowflake_session")

    # When the migration's RunPython entry runs
    migration_module.setup_snowflake_identities_schema(MagicMock(), MagicMock())

    # Then it short-circuits without opening a session
    open_sess.assert_not_called()


def test_setup_snowflake_identities_schema__configured__runs_dialect_ddl(
    mocker: MockerFixture,
) -> None:
    # Given Snowflake configured and a mocked Snowpark session
    mocker.patch.object(
        migration_module,
        "is_snowflake_configured",
        return_value=True,
    )
    sess = MagicMock()
    open_sess = mocker.patch.object(migration_module, "open_snowflake_session")
    open_sess.return_value.__enter__.return_value = sess

    # When the migration's RunPython entry runs
    migration_module.setup_snowflake_identities_schema(MagicMock(), MagicMock())

    # Then the dialect's schema DDL was executed against the session
    sess.sql.assert_called_once()
    sess.sql.return_value.collect.assert_called_once_with()
