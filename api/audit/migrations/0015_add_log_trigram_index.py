import django.contrib.postgres.indexes
import django.db.models.functions.text
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("audit", "0014_add_project_created_date_index"),
    ]

    operations = [
        TrigramExtension(),
        # The index may be created by hand on large installations ahead of
        # the deploy; without IF NOT EXISTS, the migration would then fail.
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS audit_log_upper_trgm_idx "
                    "ON audit_auditlog USING gin (UPPER(log::text) gin_trgm_ops)",
                    reverse_sql="DROP INDEX CONCURRENTLY IF EXISTS audit_log_upper_trgm_idx",
                ),
                # Without fresh statistics for the indexed expression, the
                # planner skips this index and searches with no matches walk
                # the whole project.
                migrations.RunSQL(
                    "ANALYZE audit_auditlog",
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AddIndex(
                    model_name="auditlog",
                    index=django.contrib.postgres.indexes.GinIndex(
                        django.contrib.postgres.indexes.OpClass(
                            django.db.models.functions.text.Upper("log"),
                            name="gin_trgm_ops",
                        ),
                        name="audit_log_upper_trgm_idx",
                    ),
                ),
            ],
        ),
    ]
