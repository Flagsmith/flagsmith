from django.db import migrations, models

from core.migration_helpers import PostgresOnlyRunSQL


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("code_references", "0001_code_references"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddIndex(
                    model_name="featureflagcodereferencesscan",
                    index=models.Index(
                        fields=["project", "repository_url", "-created_at"],
                        name="code_refs_project_repo_created_idx",
                    ),
                ),
            ],
            database_operations=[
                PostgresOnlyRunSQL(
                    'CREATE INDEX CONCURRENTLY IF NOT EXISTS "code_refs_project_repo_created_idx" ON "code_references_featureflagcodereferencesscan" ("project_id", "repository_url", "created_at" DESC);',
                    reverse_sql='DROP INDEX CONCURRENTLY IF EXISTS "code_refs_project_repo_created_idx"',
                ),
            ],
        ),
    ]
