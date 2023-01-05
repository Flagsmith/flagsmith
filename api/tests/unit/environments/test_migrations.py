def test_add_hide_disabled_flags_to_environmment_copies_the_setting_from_the_project(
    migrator,
):
    # Given
    old_state = migrator.apply_initial_migration(
        ("environments", "0026_add_auditable_base_class_to_environment_model")
    )

    project_model = old_state.apps.get_model("projects", "Project")
    organisation_model = old_state.apps.get_model("organisations", "Organisation")
    environment_model = old_state.apps.get_model("environments", "Environment")

    organisation = organisation_model.objects.create(name="test org")
    project_flag_disabled = project_model.objects.create(
        name="test project", organisation=organisation, hide_disabled_flags=True
    )
    environment_flag_disabled = environment_model.objects.create(
        name="test environment", project=project_flag_disabled
    )

    project_flag_enabled = project_model.objects.create(
        name="test project", organisation=organisation, hide_disabled_flags=False
    )
    environment_flag_enabled = environment_model.objects.create(
        name="test environment", project=project_flag_enabled
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("environments", "0027_add_hide_disabled_flags")
    )

    # Then
    new_environment_model = new_state.apps.get_model("environments", "Environment")
    new_environment_flag_disabled = new_environment_model.objects.get(
        pk=environment_flag_disabled.pk
    )
    new_environment_flag_enabled = new_environment_model.objects.get(
        pk=environment_flag_enabled.pk
    )
    assert new_environment_flag_disabled.hide_disabled_flags is True
    assert new_environment_flag_enabled.hide_disabled_flags is False
