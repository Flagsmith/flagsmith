from django_test_migrations.migrator import Migrator


def test_0014_drop_ingestion_infrastructure_and_delivery_log__reverse__succeeds(
    migrator: Migrator,
) -> None:
    # Given
    migrator.apply_initial_migration(
        ("experimentation", "0016_add_delivery_connections_db_view_and_status")
    )

    # When
    reversed_state = migrator.apply_tested_migration(
        ("experimentation", "0013_add_experiment_audience")
    )

    # Then
    WarehouseDeliveryLog = reversed_state.apps.get_model(
        "experimentation", "WarehouseDeliveryLog"
    )
    assert WarehouseDeliveryLog.objects.count() == 0
