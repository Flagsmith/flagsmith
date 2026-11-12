from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organisations", "0059_use_no_ssrf_url_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="organisation",
            name="targeting_key",
            field=models.CharField(
                blank=True,
                help_text=(
                    "Flagsmith-on-Flagsmith targeting key. Immutable; org.<id> "
                    "is used when unset."
                ),
                max_length=64,
                null=True,
            ),
        ),
    ]
