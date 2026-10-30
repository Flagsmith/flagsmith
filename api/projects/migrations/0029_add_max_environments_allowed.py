from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0028_add_enforce_feature_owners_to_project"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="max_environments_allowed",
            field=models.IntegerField(
                default=100,
                help_text="Max environments allowed for this project",
            ),
        ),
    ]
