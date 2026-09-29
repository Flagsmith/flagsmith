from django.db import migrations

from core.migration_helpers import PostgresOnlyRunSQL

CREATE_ENVIRONMENT_KEYS_DB_VIEW = """
CREATE VIEW experimentation_environment_keys AS
SELECT
    environment.api_key AS sdk_key,
    environment.api_key AS client_api_key,
    connection.warehouse_type <> 'flagsmith' AS uses_external_warehouse,
    NULL::timestamptz AS expires_at
FROM environments_environment AS environment
JOIN experimentation_warehouseconnection AS connection
    ON connection.environment_id = environment.id
    AND connection.deleted_at IS NULL
WHERE environment.deleted_at IS NULL
UNION ALL
SELECT
    api_key.key AS sdk_key,
    environment.api_key AS client_api_key,
    connection.warehouse_type <> 'flagsmith' AS uses_external_warehouse,
    api_key.expires_at
FROM environments_environmentapikey AS api_key
JOIN environments_environment AS environment
    ON environment.id = api_key.environment_id
JOIN experimentation_warehouseconnection AS connection
    ON connection.environment_id = environment.id
    AND connection.deleted_at IS NULL
WHERE api_key.active
    AND environment.deleted_at IS NULL;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("environments", "0039_use_no_ssrf_url_field"),
        ("experimentation", "0014_drop_ingestion_infrastructure_and_delivery_log"),
    ]

    operations = [
        PostgresOnlyRunSQL(
            CREATE_ENVIRONMENT_KEYS_DB_VIEW,
            reverse_sql="DROP VIEW IF EXISTS experimentation_environment_keys;",
        ),
    ]
