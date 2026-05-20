import hashlib
import json
from itertools import groupby
from operator import attrgetter
from typing import NamedTuple, TypedDict

import django.db.models.deletion
from django.apps.registry import Apps
from django.db import migrations, models
from django.db.models import Max


class LegacyCodeReference(TypedDict):
    feature_name: str
    file_path: str
    line_number: int


class StoredCodeReference(TypedDict):
    file_path: str
    line_number: int


def _hash_references(references: list[StoredCodeReference]) -> str:
    return hashlib.md5(
        json.dumps(references, sort_keys=True).encode(),
        usedforsecurity=False,
    ).hexdigest()


def migrate_scans_forward(apps: Apps, _: object) -> None:
    """Split each legacy scan into new cardinality (per-repository and per-feature)"""

    LegacyScan = apps.get_model("code_references", "FeatureFlagCodeReferencesScan")
    PerFeatureScan = apps.get_model("code_references", "ScannedCodeReferences")
    Repository = apps.get_model("code_references", "VCSRepository")
    Feature = apps.get_model("features", "Feature")

    legacy_scans_summaries = LegacyScan.objects.values(
        "project_id",
        "repository_url",
        "vcs_provider",
    ).annotate(last_scanned_at=Max("created_at"))

    repositories_to_create = [
        Repository(
            project_id=summary["project_id"],
            url=summary["repository_url"],
            vcs_provider=summary["vcs_provider"],
            last_scanned_at=summary["last_scanned_at"],
        )
        for summary in legacy_scans_summaries
    ]
    Repository.objects.bulk_create(repositories_to_create)
    repositories = {
        (repository.project_id, repository.url): repository
        for repository in repositories_to_create
    }

    class PerFeatureScanKey(NamedTuple):
        feature_id: int
        repository_id: int
        code_references_hash: str

    # Iteration is oldest-first, so overwriting on key collision means the
    # newest legacy scan wins for a given (feature, repository, hash).
    per_feature_rows: dict[PerFeatureScanKey, "PerFeatureScan"] = {}

    legacy_scans = LegacyScan.objects.order_by("project_id", "created_at").iterator(
        chunk_size=200,
    )
    grouped_scans = groupby(legacy_scans, key=attrgetter("project_id"))
    for project_id, project_scans in grouped_scans:
        features = {
            (feature.project_id, feature.name): feature
            for feature in Feature.objects.filter(
                project_id=project_id,
                deleted_at__isnull=True,  # Historical models drop SoftDeleteManager
            )
        }
        for legacy_scan in project_scans:
            repository = repositories[project_id, legacy_scan.repository_url]

            references_by_feature: dict[str, list[StoredCodeReference]] = {}
            for reference in legacy_scan.code_references:
                feature_name = reference["feature_name"]
                references_by_feature.setdefault(feature_name, []).append(
                    StoredCodeReference(
                        file_path=reference["file_path"],
                        line_number=reference["line_number"],
                    )
                )

            for feature_name, references in references_by_feature.items():
                if not (feature := features.get((project_id, feature_name))):
                    continue
                references_hash = _hash_references(references)
                key = PerFeatureScanKey(
                    feature_id=feature.id,
                    repository_id=repository.id,
                    code_references_hash=references_hash,
                )
                per_feature_rows[key] = PerFeatureScan(
                    feature=feature,
                    repository=repository,
                    code_references_hash=references_hash,
                    revision=legacy_scan.revision,
                    code_references=references,
                    created_at=legacy_scan.created_at,
                )

    PerFeatureScan.objects.bulk_create(
        per_feature_rows.values(),
        batch_size=1000,
    )


def migrate_scans_backward(apps: Apps, _: object) -> None:
    """Mirror each per-feature row back into the legacy single-table layout."""
    LegacyScan = apps.get_model("code_references", "FeatureFlagCodeReferencesScan")
    PerFeatureScan = apps.get_model("code_references", "ScannedCodeReferences")
    LegacyScan._meta.get_field("created_at").auto_now_add = False

    per_feature_scans = PerFeatureScan.objects.select_related(
        "repository",
        "feature",
    ).iterator(chunk_size=200)

    for per_feature_scan in per_feature_scans:
        repository = per_feature_scan.repository
        feature_name = per_feature_scan.feature.name
        LegacyScan.objects.create(
            project_id=repository.project_id,
            repository_url=repository.url,
            vcs_provider=repository.vcs_provider,
            revision=per_feature_scan.revision,
            code_references=[
                {"feature_name": feature_name, **reference}
                for reference in per_feature_scan.code_references
            ],
            created_at=per_feature_scan.created_at,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("code_references", "0002_add_project_repo_created_index"),
        ("features", "0066_constrain_feature_type"),
        ("projects", "0029_bump_default_project_limits"),
    ]

    operations = [
        migrations.CreateModel(
            name="VCSRepository",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("url", models.URLField()),
                (
                    "vcs_provider",
                    models.CharField(
                        choices=[("github", "GitHub")],
                        max_length=50,
                    ),
                ),
                ("last_scanned_at", models.DateTimeField(null=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vcs_repositories",
                        to="projects.project",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="vcsrepository",
            constraint=models.UniqueConstraint(
                fields=("project", "url"),
                name="unique_vcs_repository",
            ),
        ),
        migrations.CreateModel(
            name="ScannedCodeReferences",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField()),
                ("revision", models.CharField(max_length=100)),
                ("code_references", models.JSONField(default=list)),
                ("code_references_hash", models.CharField(max_length=32)),
                (
                    "feature",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scanned_code_references",
                        to="features.feature",
                    ),
                ),
                (
                    "repository",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scanned_code_references",
                        to="code_references.vcsrepository",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="scannedcodereferences",
            constraint=models.UniqueConstraint(
                fields=("feature", "repository", "code_references_hash"),
                name="unique_scanned_code_references",
            ),
        ),
        migrations.AddIndex(
            model_name="scannedcodereferences",
            index=models.Index(
                fields=("feature", "repository", "created_at"),
                name="cr_feature_repo_created_idx",
            ),
        ),
        migrations.RunPython(
            code=migrate_scans_forward,
            reverse_code=migrate_scans_backward,
        ),
        migrations.DeleteModel(
            name="FeatureFlagCodeReferencesScan",
        ),
    ]
