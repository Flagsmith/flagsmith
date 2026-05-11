import freezegun
import pytest
from django.conf import settings as test_settings
from django.utils import timezone
from django_test_migrations.migrator import Migrator

pytestmark = pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)


_INITIAL = ("code_references", "0002_add_project_repo_created_index")
_TARGET = ("code_references", "0003_introduce_per_feature_scanned_references")


def test_introduce_per_feature_scanned_references_forward__legacy_scan_with_multiple_features__splits_into_per_feature_rows_with_stripped_shape(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    feature_one = Feature.objects.create(name="feature-1", project=project)
    feature_two = Feature.objects.create(name="feature-2", project=project)
    LegacyScan.objects.create(
        project=project,
        repository_url="https://github.flagsmith.com/backend",
        vcs_provider="github",
        revision="rev-1",
        code_references=[
            {"feature_name": "feature-1", "file_path": "a.py", "line_number": 1},
            {"feature_name": "feature-1", "file_path": "b.py", "line_number": 2},
            {"feature_name": "feature-2", "file_path": "c.py", "line_number": 3},
        ],
    )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    Repository = new_state.apps.get_model("code_references", "VCSRepository")
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    repository = Repository.objects.get()
    assert repository.url == "https://github.flagsmith.com/backend"
    assert repository.vcs_provider == "github"
    assert {
        scan.feature_id: scan.code_references for scan in PerFeatureScan.objects.all()
    } == {
        feature_one.id: [
            {"file_path": "a.py", "line_number": 1},
            {"file_path": "b.py", "line_number": 2},
        ],
        feature_two.id: [{"file_path": "c.py", "line_number": 3}],
    }


def test_introduce_per_feature_scanned_references_forward__same_content_repeated_across_scans__deduplicates_and_consolidates_repository(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    Feature.objects.create(name="feature-1", project=project)
    identical_references = [
        {"feature_name": "feature-1", "file_path": "a.py", "line_number": 1},
    ]
    with freezegun.freeze_time("2099-01-01T10:00:00+00:00"):
        LegacyScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/backend",
            vcs_provider="github",
            revision="older-revision",
            code_references=identical_references,
        )
    with freezegun.freeze_time("2099-01-03T10:00:00+00:00"):
        LegacyScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/backend",
            vcs_provider="github",
            revision="newer-revision",
            code_references=identical_references,
        )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    Repository = new_state.apps.get_model("code_references", "VCSRepository")
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    repository = Repository.objects.get()
    assert repository.last_scanned_at.isoformat() == "2099-01-03T10:00:00+00:00"
    scan = PerFeatureScan.objects.get()
    assert scan.revision == "newer-revision"


def test_introduce_per_feature_scanned_references_forward__different_content_across_scans__creates_separate_rows(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    Feature.objects.create(name="feature-1", project=project)
    for revision, file_path in [("rev-1", "a.py"), ("rev-2", "b.py")]:
        LegacyScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/backend",
            vcs_provider="github",
            revision=revision,
            code_references=[
                {"feature_name": "feature-1", "file_path": file_path, "line_number": 1},
            ],
        )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    assert PerFeatureScan.objects.count() == 2


def test_introduce_per_feature_scanned_references_forward__multiple_repositories_per_project__creates_distinct_repositories(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    Feature.objects.create(name="feature-1", project=project)
    for repository_url in [
        "https://github.flagsmith.com/backend",
        "https://github.flagsmith.com/frontend",
    ]:
        LegacyScan.objects.create(
            project=project,
            repository_url=repository_url,
            vcs_provider="github",
            revision="rev-1",
            code_references=[
                {"feature_name": "feature-1", "file_path": "a.py", "line_number": 1},
            ],
        )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    Repository = new_state.apps.get_model("code_references", "VCSRepository")
    assert {repository.url for repository in Repository.objects.all()} == {
        "https://github.flagsmith.com/backend",
        "https://github.flagsmith.com/frontend",
    }


def test_introduce_per_feature_scanned_references_forward__feature_name_collision_across_projects__matches_only_within_project(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project_a = Project.objects.create(name="Project A", organisation=organisation)
    project_b = Project.objects.create(name="Project B", organisation=organisation)
    feature_in_project_a = Feature.objects.create(name="shared", project=project_a)
    Feature.objects.create(name="shared", project=project_b)
    LegacyScan.objects.create(
        project=project_a,
        repository_url="https://github.flagsmith.com/backend",
        vcs_provider="github",
        revision="rev-1",
        code_references=[
            {"feature_name": "shared", "file_path": "a.py", "line_number": 1},
        ],
    )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    scan = PerFeatureScan.objects.get()
    assert scan.feature_id == feature_in_project_a.id


def test_introduce_per_feature_scanned_references_forward__reference_to_unknown_feature_name__skipped(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    surviving_feature = Feature.objects.create(name="alive", project=project)
    LegacyScan.objects.create(
        project=project,
        repository_url="https://github.flagsmith.com/backend",
        vcs_provider="github",
        revision="rev-1",
        code_references=[
            {"feature_name": "alive", "file_path": "a.py", "line_number": 1},
            {"feature_name": "unknown", "file_path": "u.py", "line_number": 2},
        ],
    )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    scan = PerFeatureScan.objects.get()
    assert scan.feature_id == surviving_feature.id


def test_introduce_per_feature_scanned_references_forward__live_feature_with_soft_deleted_shadow__matches_only_the_live_feature(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    Feature.objects.create(
        name="feature-1",
        project=project,
        deleted_at=timezone.now(),
    )
    live_feature = Feature.objects.create(name="feature-1", project=project)
    LegacyScan.objects.create(
        project=project,
        repository_url="https://github.flagsmith.com/backend",
        vcs_provider="github",
        revision="rev-1",
        code_references=[
            {"feature_name": "feature-1", "file_path": "a.py", "line_number": 1},
        ],
    )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    scan = PerFeatureScan.objects.get()
    assert scan.feature_id == live_feature.id


def test_introduce_per_feature_scanned_references_forward__per_feature_row__preserves_legacy_created_at(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(_INITIAL)
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    LegacyScan = old_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    Feature.objects.create(name="feature-1", project=project)
    with freezegun.freeze_time("2099-01-01T10:00:00+00:00"):
        LegacyScan.objects.create(
            project=project,
            repository_url="https://github.flagsmith.com/backend",
            vcs_provider="github",
            revision="rev-1",
            code_references=[
                {"feature_name": "feature-1", "file_path": "a.py", "line_number": 1},
            ],
        )

    # When
    new_state = migrator.apply_tested_migration(_TARGET)

    # Then
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )
    scan = PerFeatureScan.objects.get()
    assert scan.created_at.isoformat() == "2099-01-01T10:00:00+00:00"


def test_introduce_per_feature_scanned_references_backward__per_feature_row__rebuilds_legacy_scan_with_feature_name_and_repository_fields(
    migrator: Migrator,
) -> None:
    # Given
    new_state = migrator.apply_initial_migration(_TARGET)
    Organisation = new_state.apps.get_model("organisations", "Organisation")
    Project = new_state.apps.get_model("projects", "Project")
    Feature = new_state.apps.get_model("features", "Feature")
    Repository = new_state.apps.get_model("code_references", "VCSRepository")
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    feature_one = Feature.objects.create(name="feature-1", project=project)
    feature_two = Feature.objects.create(name="feature-2", project=project)
    repository = Repository.objects.create(
        project=project,
        url="https://github.flagsmith.com/backend",
        vcs_provider="github",
    )
    for feature, file_path, hash_id in [
        (feature_one, "a.py", "hash-1"),
        (feature_two, "b.py", "hash-2"),
    ]:
        PerFeatureScan.objects.create(
            feature=feature,
            repository=repository,
            revision="rev-1",
            code_references=[{"file_path": file_path, "line_number": 1}],
            code_references_hash=hash_id,
        )

    # When
    reverted_state = migrator.apply_tested_migration(_INITIAL)

    # Then
    LegacyScan = reverted_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )
    assert {
        scan.code_references[0]["feature_name"]: (
            scan.revision,
            scan.repository_url,
            scan.vcs_provider,
            scan.code_references,
        )
        for scan in LegacyScan.objects.all()
    } == {
        "feature-1": (
            "rev-1",
            "https://github.flagsmith.com/backend",
            "github",
            [{"feature_name": "feature-1", "file_path": "a.py", "line_number": 1}],
        ),
        "feature-2": (
            "rev-1",
            "https://github.flagsmith.com/backend",
            "github",
            [{"feature_name": "feature-2", "file_path": "b.py", "line_number": 1}],
        ),
    }


def test_introduce_per_feature_scanned_references_backward__legacy_row__preserves_per_feature_created_at(
    migrator: Migrator,
) -> None:
    # Given
    new_state = migrator.apply_initial_migration(_TARGET)
    Organisation = new_state.apps.get_model("organisations", "Organisation")
    Project = new_state.apps.get_model("projects", "Project")
    Feature = new_state.apps.get_model("features", "Feature")
    Repository = new_state.apps.get_model("code_references", "VCSRepository")
    PerFeatureScan = new_state.apps.get_model(
        "code_references", "ScannedCodeReferences"
    )

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    feature = Feature.objects.create(name="feature-1", project=project)
    repository = Repository.objects.create(
        project=project,
        url="https://github.flagsmith.com/backend",
        vcs_provider="github",
    )
    with freezegun.freeze_time("2099-01-01T10:00:00+00:00"):
        PerFeatureScan.objects.create(
            feature=feature,
            repository=repository,
            revision="rev-1",
            code_references=[{"file_path": "a.py", "line_number": 1}],
            code_references_hash="hash-1",
        )

    # When
    reverted_state = migrator.apply_tested_migration(_INITIAL)

    # Then
    LegacyScan = reverted_state.apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )
    legacy_scan = LegacyScan.objects.get()
    assert legacy_scan.created_at.isoformat() == "2099-01-01T10:00:00+00:00"
