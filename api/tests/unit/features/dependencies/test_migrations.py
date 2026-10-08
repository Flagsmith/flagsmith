from django_test_migrations.migrator import Migrator


def test_delete_draft_segment_flag_references__draft_and_live_segments__deletes_draft_references_only(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_dependencies", "0001_initial")
    )
    organisation = old_state.apps.get_model(
        "organisations", "Organisation"
    ).objects.create(name="Test Organisation")
    project = old_state.apps.get_model("projects", "Project").objects.create(
        name="Test Project", organisation=organisation
    )
    environment = old_state.apps.get_model(
        "environments", "Environment"
    ).objects.create(name="Test Environment", project=project)
    change_request = old_state.apps.get_model(
        "workflows_core", "ChangeRequest"
    ).objects.create(environment=environment, title="Test CR", user_id=None)
    feature = old_state.apps.get_model("features", "Feature").objects.create(
        name="payments", project=project
    )
    segment_model = old_state.apps.get_model("segments", "Segment")
    live_segment = segment_model.objects.create(name="live", project=project)
    draft_segment = segment_model.objects.create(
        name="draft", project=project, change_request=change_request
    )
    reference_model = old_state.apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )
    for segment in (live_segment, draft_segment):
        reference_model.objects.create(
            segment=segment,
            prerequisite_feature=feature,
            condition_json_path="$[0].conditions[0]",
        )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_dependencies", "0002_delete_draft_segment_flag_references")
    )

    # Then
    new_reference_model = new_state.apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )
    assert list(new_reference_model.objects.values_list("segment_id", flat=True)) == [
        live_segment.id
    ]
