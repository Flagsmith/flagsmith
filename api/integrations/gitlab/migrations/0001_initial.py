import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("projects", "0027_add_create_project_level_change_requests_permission"),
    ]

    operations = [
        migrations.CreateModel(
            name="GitLabConfiguration",
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
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "gitlab_instance_url",
                    models.URLField(
                        help_text="Base URL of the GitLab instance, e.g. https://gitlab.com",
                        max_length=200,
                    ),
                ),
                (
                    "access_token",
                    models.CharField(
                        help_text="GitLab Group or Project Access Token with api scope",
                        max_length=255,
                    ),
                ),
                (
                    "webhook_secret",
                    models.CharField(
                        help_text="Secret token for validating incoming GitLab webhooks",
                        max_length=255,
                    ),
                ),
                (
                    "gitlab_project_id",
                    models.IntegerField(
                        blank=True,
                        help_text="GitLab's numeric project ID",
                        null=True,
                    ),
                ),
                (
                    "project_name",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="GitLab project path with namespace, e.g. my-group/my-project",
                        max_length=200,
                    ),
                ),
                (
                    "tagging_enabled",
                    models.BooleanField(default=False),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gitlab_project",
                        to="projects.project",
                    ),
                ),
            ],
            options={
                "ordering": ("id",),
            },
        ),
        migrations.AddConstraint(
            model_name="gitlabconfiguration",
            constraint=models.UniqueConstraint(
                condition=models.Q(deleted_at__isnull=True),
                fields=("project",),
                name="gitlabconf_project_id_idx",
            ),
        ),
    ]
