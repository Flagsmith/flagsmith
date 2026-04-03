from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tags", "0008_alter_tag_type"),
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
                    ("GITLAB", "Gitlab"),
                    ("UNHEALTHY", "Unhealthy"),
                ],
                default="NONE",
                help_text=(
                    "Field used to provide a consistent identifier for "
                    "the FE and API to use for business logic."
                ),
                max_length=100,
            ),
        ),
    ]
