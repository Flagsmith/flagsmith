import pytest
from django.conf import settings
from django_test_migrations.migrator import Migrator

pytestmark = pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)


def test_0039_ffadminuser_first_name_v2__values_expected(migrator: Migrator) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("users", "0038_create_hubspot_tracker")
    )
    OldFFAdminUser = old_state.apps.get_model("users", "FFAdminUser")

    user = OldFFAdminUser.objects.create(first_name="Testfirstname")

    # When
    new_state = migrator.apply_tested_migration(
        ("users", "0039_ffadminuser_first_name_v2")
    )
    NewFFAdminUser = new_state.apps.get_model("users", "FFAdminUser")

    # Then
    assert NewFFAdminUser.objects.get(id=user.id).first_name == user.first_name


def test_0039_ffadminuser_first_name_v2__reverse__values_expected(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("users", "0039_ffadminuser_first_name_v2")
    )
    NewFFAdminUser = old_state.apps.get_model("users", "FFAdminUser")

    user = NewFFAdminUser.objects.create(
        first_name="TestfirstnameTestfirstnameTestfirstnameTestfirstname"
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("users", "0038_create_hubspot_tracker")
    )
    OldFFAdminUser = new_state.apps.get_model("users", "FFAdminUser")

    # Then
    assert (
        OldFFAdminUser.objects.get(id=user.id).first_name
        == "TestfirstnameTestfirstnameTest"
    )
