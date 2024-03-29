# Generated by Django 3.2.23 on 2024-02-05 16:53

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organisations', '0050_add_historical_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='organisationsubscriptioninformationcache',
            name='current_billing_term_ends_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='organisationsubscriptioninformationcache',
            name='current_billing_term_starts_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.CreateModel(
            name='OranisationAPIUsageNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percent_usage', models.IntegerField(validators=[django.core.validators.MinValueValidator(75), django.core.validators.MaxValueValidator(120)])),
                ('notified_at', models.DateTimeField(null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('organisation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_usage_notifications', to='organisations.organisation')),
            ],
        ),
    ]
