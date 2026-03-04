from django.contrib.postgres.indexes import GinIndex
from django.db import migrations

from core.migration_helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("code_references", "0003_add_feature_names"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name="featureflagcodereferencesscan",
                    index=GinIndex(
                        fields=["feature_names"],
                        name="code_refs_feat_names_gin_idx",
                    ),
                ),
            ],
            database_operations=[
                PostgresOnlyRunSQL(
                    'CREATE INDEX CONCURRENTLY IF NOT EXISTS "code_refs_feat_names_gin_idx" '
                    'ON "code_references_featureflagcodereferencesscan" USING gin ("feature_names");',
                    reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "code_refs_feat_names_gin_idx"',
                ),
            ],
        ),
    ]
