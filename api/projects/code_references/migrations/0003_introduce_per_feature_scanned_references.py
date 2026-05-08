import django.db.models.deletion
from django.db import migrations, models


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
                ("created_at", models.DateTimeField(auto_now_add=True)),
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
        migrations.DeleteModel(
            name="FeatureFlagCodeReferencesScan",
        ),
    ]
