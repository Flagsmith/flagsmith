from django_test_migrations.migrator import Migrator


def test_backfill_feature_names(migrator: Migrator) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("code_references", "0002_add_project_repo_created_index")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    FeatureFlagCodeReferencesScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test Project", organisation=organisation)

    # A scan with references to multiple features (unsorted) including a duplicate
    scan_with_references = FeatureFlagCodeReferencesScan.objects.create(
        project=project,
        repository_url="https://github.com/example/repo",
        revision="abc123",
        code_references=[
            {"feature_name": "zebra_flag", "file_path": "foo.py", "line_number": 1},
            {"feature_name": "alpha_flag", "file_path": "bar.py", "line_number": 2},
            {"feature_name": "zebra_flag", "file_path": "baz.py", "line_number": 3},
        ],
    )

    # A scan with no code references
    scan_with_no_references = FeatureFlagCodeReferencesScan.objects.create(
        project=project,
        repository_url="https://github.com/example/repo",
        revision="def456",
        code_references=[],
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("code_references", "0003_add_feature_names")
    )
    NewScan = new_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    # Then
    # Duplicates are removed and names are sorted
    updated_scan = NewScan.objects.get(id=scan_with_references.id)
    assert updated_scan.feature_names == ["alpha_flag", "zebra_flag"]

    # Empty code_references results in empty feature_names
    updated_scan_no_refs = NewScan.objects.get(id=scan_with_no_references.id)
    assert updated_scan_no_refs.feature_names == []
