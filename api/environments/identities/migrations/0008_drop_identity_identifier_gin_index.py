from common.migrations.helpers import PostgresOnlyRunSQL
from django.db import migrations


class Migration(migrations.Migration):
    # DROP INDEX CONCURRENTLY can't run inside a transaction.
    atomic = False

    dependencies = [
        ("identities", "0007_identity_system_traits"),
    ]

    operations = [
        # `identity_identifier_idx` was added by a migration that was reverted
        # without dropping the index, and it was also created by hand on some
        # databases. Where it exists, it can derail query plans for identity
        # searches. Nothing in the model state refers to it, so this is a
        # database-only operation, and a no-op where the index doesn't exist.
        PostgresOnlyRunSQL(
            "DROP INDEX CONCURRENTLY IF EXISTS identity_identifier_idx",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
