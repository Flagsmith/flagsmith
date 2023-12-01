import pytest
from django.conf import settings


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_migrate_use_mv_v2_evaluation(migrator):
    # Given
    old_state = migrator.apply_initial_migration(
        ("environments", "0027_auto_20230106_0626")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Environment = old_state.apps.get_model("environments", "Environment")

    # setup some test data
    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    environment_1 = Environment.objects.create(
        name="Test environment 1", project=project
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("environments", "0028_add_use_mv_v2_evaluation")
    )
    NewEnvironment = new_state.apps.get_model("environments", "Environment")

    # Then
    # `use_mv_v2_evaluation` is set to false
    assert NewEnvironment.objects.get(id=environment_1.id).use_mv_v2_evaluation is False

    # and if we create a new environment it should have `use_mv_v2_evaluation` set to True
    new_environment = NewEnvironment.objects.create(
        name="Test environment 3", project_id=project.id
    )
    assert new_environment.use_mv_v2_evaluation is True
