import pytest
from django.db import connections
from django_test_migrations.migrator import Migrator

pytestmark = pytest.mark.use_analytics_db


def test_0008_labels_jsonb__fresh_install__preserves_data(
    analytics_migrator: Migrator,
) -> None:
    """Test migration on fresh install where labels are already JSONField.

    0006 creates labels as JSONField, so 0008's SQL is a no-op
    (the conditional loop finds no hstore columns). This test verifies
    the PL/pgSQL block is syntactically valid and data is preserved.
    """
    # Given - state at 0007 (labels columns exist as JSONField)
    old_state = analytics_migrator.apply_initial_migration(
        ("app_analytics", "0007_rename_environment_id_created_at_index"),
    )

    APIUsageRaw = old_state.apps.get_model("app_analytics", "APIUsageRaw")
    APIUsageBucket = old_state.apps.get_model("app_analytics", "APIUsageBucket")
    FeatureEvaluationRaw = old_state.apps.get_model(
        "app_analytics", "FeatureEvaluationRaw"
    )
    FeatureEvaluationBucket = old_state.apps.get_model(
        "app_analytics", "FeatureEvaluationBucket"
    )

    # Create records with labels
    labels = {"sdk_type": "python", "sdk_version": "3.0.0"}
    api_raw = APIUsageRaw.objects.using("analytics").create(
        environment_id=1, host="test", resource=1, labels=labels
    )
    api_bucket = APIUsageBucket.objects.using("analytics").create(
        environment_id=1,
        bucket_size=15,
        created_at="2025-01-01T00:00:00Z",
        total_count=10,
        resource=1,
        labels=labels,
    )
    fe_raw = FeatureEvaluationRaw.objects.using("analytics").create(
        feature_name="test_feature",
        environment_id=1,
        evaluation_count=5,
        labels=labels,
    )
    fe_bucket = FeatureEvaluationBucket.objects.using("analytics").create(
        environment_id=1,
        bucket_size=15,
        created_at="2025-01-01T00:00:00Z",
        total_count=10,
        feature_name="test_feature",
        labels=labels,
    )

    # When - apply the jsonb migration
    new_state = analytics_migrator.apply_tested_migration(
        ("app_analytics", "0008_labels_jsonb"),
    )

    # Then - all records and their labels are preserved
    NewAPIUsageRaw = new_state.apps.get_model("app_analytics", "APIUsageRaw")
    NewAPIUsageBucket = new_state.apps.get_model("app_analytics", "APIUsageBucket")
    NewFeatureEvaluationRaw = new_state.apps.get_model(
        "app_analytics", "FeatureEvaluationRaw"
    )
    NewFeatureEvaluationBucket = new_state.apps.get_model(
        "app_analytics", "FeatureEvaluationBucket"
    )

    assert NewAPIUsageRaw.objects.using("analytics").get(id=api_raw.id).labels == labels
    assert (
        NewAPIUsageBucket.objects.using("analytics").get(id=api_bucket.id).labels
        == labels
    )
    assert (
        NewFeatureEvaluationRaw.objects.using("analytics").get(id=fe_raw.id).labels
        == labels
    )
    assert (
        NewFeatureEvaluationBucket.objects.using("analytics")
        .get(id=fe_bucket.id)
        .labels
        == labels
    )


def test_0008_labels_jsonb__hstore_columns__converts_to_jsonb(
    analytics_migrator: Migrator,
) -> None:
    """Test migration converts existing hstore columns to jsonb.

    Simulates the upgrade path for installations that ran the original
    0006 migration which created labels as HStoreField.
    """
    # Given - state at 0007 (labels columns exist as JSONField in Django state)
    expected_tables = [
        "app_analytics_apiusagebucket",
        "app_analytics_apiusageraw",
        "app_analytics_featureevaluationbucket",
        "app_analytics_featureevaluationraw",
    ]

    analytics_migrator.apply_initial_migration(
        ("app_analytics", "0007_rename_environment_id_created_at_index"),
    )

    # Simulate the original 0006 migration having created hstore columns
    # by converting the jsonb columns back to hstore at the database level.
    connection = connections["analytics"]
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS hstore")
        for table in expected_tables:
            cursor.execute(
                f"ALTER TABLE {table} "
                f"ALTER COLUMN labels TYPE hstore USING labels::text::hstore, "
                f"ALTER COLUMN labels SET DEFAULT ''::hstore"
            )

        # Insert data as hstore values
        cursor.execute(
            "INSERT INTO app_analytics_apiusageraw "
            "(environment_id, host, resource, count, labels, created_at) "
            'VALUES (1, \'test\', 1, 1, \'"sdk_type"=>"python", "sdk_version"=>"3.0.0"\'::hstore, NOW()) '
            "RETURNING id"
        )
        api_raw_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO app_analytics_apiusagebucket "
            "(environment_id, bucket_size, created_at, total_count, resource, labels) "
            'VALUES (1, 15, \'2025-01-01T00:00:00Z\', 10, 1, \'"sdk_type"=>"python", "sdk_version"=>"3.0.0"\'::hstore) '
            "RETURNING id"
        )
        api_bucket_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO app_analytics_featureevaluationraw "
            "(feature_name, environment_id, evaluation_count, labels, created_at) "
            'VALUES (\'test_feature\', 1, 5, \'"sdk_type"=>"python", "sdk_version"=>"3.0.0"\'::hstore, NOW()) '
            "RETURNING id"
        )
        fe_raw_id = cursor.fetchone()[0]

        cursor.execute(
            "INSERT INTO app_analytics_featureevaluationbucket "
            "(environment_id, bucket_size, created_at, total_count, feature_name, labels) "
            'VALUES (1, 15, \'2025-01-01T00:00:00Z\', 10, \'test_feature\', \'"sdk_type"=>"python", "sdk_version"=>"3.0.0"\'::hstore) '
            "RETURNING id"
        )
        fe_bucket_id = cursor.fetchone()[0]

    # When - apply the jsonb migration
    new_state = analytics_migrator.apply_tested_migration(
        ("app_analytics", "0008_labels_jsonb"),
    )

    # Then - columns are now jsonb and data is preserved
    expected_labels = {"sdk_type": "python", "sdk_version": "3.0.0"}

    with connection.cursor() as cursor:
        for table in expected_tables:
            cursor.execute(
                """
                SELECT t.typname
                FROM pg_class c
                JOIN pg_attribute a ON a.attrelid = c.oid
                JOIN pg_type t ON a.atttypid = t.oid
                WHERE c.relname = %s AND a.attname = %s
                """,
                [table, "labels"],
            )
            assert cursor.fetchone()[0] == "jsonb"

    NewAPIUsageRaw = new_state.apps.get_model("app_analytics", "APIUsageRaw")
    NewAPIUsageBucket = new_state.apps.get_model("app_analytics", "APIUsageBucket")
    NewFeatureEvaluationRaw = new_state.apps.get_model(
        "app_analytics", "FeatureEvaluationRaw"
    )
    NewFeatureEvaluationBucket = new_state.apps.get_model(
        "app_analytics", "FeatureEvaluationBucket"
    )

    assert (
        NewAPIUsageRaw.objects.using("analytics").get(id=api_raw_id).labels
        == expected_labels
    )
    assert (
        NewAPIUsageBucket.objects.using("analytics").get(id=api_bucket_id).labels
        == expected_labels
    )
    assert (
        NewFeatureEvaluationRaw.objects.using("analytics").get(id=fe_raw_id).labels
        == expected_labels
    )
    assert (
        NewFeatureEvaluationBucket.objects.using("analytics")
        .get(id=fe_bucket_id)
        .labels
        == expected_labels
    )
