"""Create the canonical IDENTITIES table the SQL flag engine emits
against when a Snowflake account is configured.

No-op when SNOWFLAKE_* settings are unset, so self-hosted installs
without Snowflake (and the test suite) migrate cleanly.
"""

from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from flagsmith_sql_flag_engine.dialects import SnowflakeDialect

from segment_membership.services import (
    is_snowflake_configured,
    open_snowflake_session,
)


def setup_snowflake_identities_schema(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    if not is_snowflake_configured():
        return
    with open_snowflake_session() as sess:
        sess.sql(SnowflakeDialect.schema_ddl).collect()


class Migration(migrations.Migration):
    # The Snowflake DDL talks to a remote service; running it inside
    # Django's default-atomic migration block would couple this Postgres
    # migration to a Snowflake transaction we don't actually need.
    atomic = False

    dependencies = [
        ("segment_membership", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            setup_snowflake_identities_schema,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
