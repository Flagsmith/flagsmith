from projects.code_references.models import FeatureFlagCodeReferencesScan
from projects.models import Project


def test_FeatureFlagCodeReferencesScan__save__populates_feature_names(
    project: Project,
) -> None:
    # Given
    scan = FeatureFlagCodeReferencesScan(
        project=project,
        repository_url="https://github.com/test/repo",
        revision="abc123",
        code_references=[
            {"feature_name": "feature-a", "file_path": "src/a.py", "line_number": 1},
            {"feature_name": "feature-b", "file_path": "src/b.py", "line_number": 2},
        ],
    )

    # When
    scan.save()

    # Then
    assert scan.feature_names == ["feature-a", "feature-b"]


def test_FeatureFlagCodeReferencesScan__save__deduplicates_feature_names(
    project: Project,
) -> None:
    # Given - feature-a referenced in two files
    scan = FeatureFlagCodeReferencesScan(
        project=project,
        repository_url="https://github.com/test/repo",
        revision="abc123",
        code_references=[
            {"feature_name": "feature-a", "file_path": "src/a.py", "line_number": 1},
            {"feature_name": "feature-a", "file_path": "src/a.py", "line_number": 5},
            {"feature_name": "feature-b", "file_path": "src/b.py", "line_number": 2},
        ],
    )

    # When
    scan.save()

    # Then
    assert scan.feature_names == ["feature-a", "feature-b"]


def test_FeatureFlagCodeReferencesScan__save__sets_empty_feature_names_for_empty_code_references(
    project: Project,
) -> None:
    # Given
    scan = FeatureFlagCodeReferencesScan(
        project=project,
        repository_url="https://github.com/test/repo",
        revision="abc123",
        code_references=[],
    )

    # When
    scan.save()

    # Then
    assert scan.feature_names == []
