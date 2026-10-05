from datetime import datetime, timezone

from django_test_migrations.migrator import Migrator


def test_remove_snowflake_warehouse_type__snowflake_connections_exist__soft_deletes_active_ones(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("experimentation", "0016_add_delivery_connections_db_view_and_status"),
    )
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Environment = old_state.apps.get_model("environments", "Environment")
    WarehouseConnection = old_state.apps.get_model(
        "experimentation", "WarehouseConnection"
    )
    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    snowflake_environment = Environment.objects.create(
        name="Snowflake", project=project
    )
    flagsmith_environment = Environment.objects.create(
        name="Flagsmith", project=project
    )
    previously_deleted_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    previously_deleted = WarehouseConnection.objects.create(
        environment=snowflake_environment,
        warehouse_type="snowflake",
        name="Old Snowflake",
        deleted_at=previously_deleted_at,
    )
    active_snowflake = WarehouseConnection.objects.create(
        environment=snowflake_environment,
        warehouse_type="snowflake",
        name="Snowflake",
        config={"account_identifier": "xy12345.us-east-1"},
    )
    flagsmith = WarehouseConnection.objects.create(
        environment=flagsmith_environment,
        warehouse_type="flagsmith",
        name="Flagsmith",
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("experimentation", "0017_remove_snowflake_warehouse_type"),
    )

    # Then
    NewWarehouseConnection = new_state.apps.get_model(
        "experimentation", "WarehouseConnection"
    )
    assert (
        NewWarehouseConnection.objects.get(id=active_snowflake.id).deleted_at
        is not None
    )
    assert (
        NewWarehouseConnection.objects.get(id=previously_deleted.id).deleted_at
        == previously_deleted_at
    )
    assert NewWarehouseConnection.objects.get(id=flagsmith.id).deleted_at is None
