from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gitlab", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="gitlabconfiguration",
            name="labeling_enabled",
            field=models.BooleanField(default=False),
        ),
    ]
