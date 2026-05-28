from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tags", "0009_add_gitlab_tag_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tag",
            name="type",
            field=models.CharField(
                choices=[
                    ("NONE", "None"),
                    ("STALE", "Stale"),
                    ("GITHUB", "Github"),
                    ("UNHEALTHY", "Unhealthy"),
                    ("GITLAB", "Gitlab"),
                    ("AZURE_DEVOPS", "Azure Devops"),
                ],
                default="NONE",
                help_text="Field used to provide a consistent identifier for the FE and API to use for business logic.",
                max_length=100,
            ),
        ),
    ]
