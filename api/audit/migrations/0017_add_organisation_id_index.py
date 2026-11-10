from django.db import migrations
from django.db.backends import utils as backend_utils

# Matches the name Django generates for a `db_index=True` index on this column
ORGANISATION_ID_INDEX_NAME = "audit_auditlog_organisation_id_" + (
    backend_utils.names_digest(  # type: ignore[attr-defined]  # Missing from django-stubs
        "audit_auditlog", "organisation_id", length=8
    )
)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("audit", "0016_add_organisation_id"),
    ]

    operations = [
        migrations.RunSQL(
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {ORGANISATION_ID_INDEX_NAME} "
            "ON audit_auditlog (organisation_id)",
            reverse_sql=f"DROP INDEX CONCURRENTLY IF EXISTS {ORGANISATION_ID_INDEX_NAME}",
        ),
    ]
