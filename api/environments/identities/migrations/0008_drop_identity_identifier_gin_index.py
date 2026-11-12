from common.migrations.helpers import PostgresOnlyRunSQL
from django.db import migrations


class Migration(migrations.Migration):
    # DROP INDEX CONCURRENTLY can't run inside a transaction.
    atomic = False

    dependencies = [
        ("identities", "0007_identity_system_traits"),
    ]

    operations = [
        PostgresOnlyRunSQL(
            "DROP INDEX CONCURRENTLY IF EXISTS identity_identifier_idx",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
