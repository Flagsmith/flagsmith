from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gitlab", "0002_add_gitlab_webhook_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="gitlabconfiguration",
            name="labeling_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
