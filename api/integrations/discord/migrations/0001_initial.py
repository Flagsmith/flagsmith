import uuid

import django.db.models.deletion
import django_lifecycle.mixins  # type: ignore[import-untyped]
from django.db import migrations, models

import core.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("projects", "0029_bump_default_project_limits"),
    ]

    operations = [
        migrations.CreateModel(
            name="DiscordConfiguration",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("deleted_at", models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("base_url", core.fields.NoSSRFURLField(null=True)),
                ("api_key", models.CharField(blank=True, default="", max_length=100)),
                ("project", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="discord_config", to="projects.project")),
            ],
            options={
                "abstract": False,
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
        ),
    ]
