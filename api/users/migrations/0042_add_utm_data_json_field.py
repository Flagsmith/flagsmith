# Generated by Django 4.2.22 on 2025-07-02 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0041_add_onboarding_field"),
    ]

    operations = [
        migrations.AddField(
            model_name="hubspottracker",
            name="utm_data",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
