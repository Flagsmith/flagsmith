import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gitlab", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GitLabWebhook",
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
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        default=None,
                        editable=False,
                        null=True,
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                ("gitlab_project_id", models.PositiveIntegerField()),
                ("gitlab_path_with_namespace", models.TextField()),
                ("gitlab_hook_id", models.PositiveIntegerField()),
                ("secret", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "gitlab_configuration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="webhooks",
                        to="gitlab.gitlabconfiguration",
                    ),
                ),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("gitlab_configuration", "gitlab_path_with_namespace"),
                        name="unique_gitlab_webhook_per_config_path",
                        condition=models.Q(deleted_at__isnull=True),
                    ),
                ],
            },
        ),
    ]
