# Generated by Django 3.2.17 on 2023-02-14 11:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models  # type: ignore[import-untyped]


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api_keys', '0002_soft_delete_api_keys'),
        ('segments', '0018_soft_delete_segments'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalsegment',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical segment'},
        ),
        migrations.AddField(
            model_name='condition',
            name='created_with_segment',
            field=models.BooleanField(default=False, help_text='Field to denote whether a condition was created along with segment or added after creation.'),
        ),
        migrations.AlterField(
            model_name='historicalsegment',
            name='history_date',
            field=models.DateTimeField(),
        ),
        migrations.CreateModel(
            name='HistoricalCondition',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('operator', models.CharField(choices=[('EQUAL', 'Exactly Matches'), ('GREATER_THAN', 'Greater than'), ('LESS_THAN', 'Less than'), ('CONTAINS', 'Contains'), ('GREATER_THAN_INCLUSIVE', 'Greater than or equal to'), ('LESS_THAN_INCLUSIVE', 'Less than or equal to'), ('NOT_CONTAINS', 'Does not contain'), ('NOT_EQUAL', 'Does not match'), ('REGEX', 'Matches regex'), ('PERCENTAGE_SPLIT', 'Percentage split'), ('MODULO', 'Modulo Operation'), ('IS_SET', 'Is set'), ('IS_NOT_SET', 'Is not set'), ('IN', 'In')], max_length=500)),
                ('property', models.CharField(blank=True, max_length=1000, null=True)),
                ('value', models.CharField(blank=True, max_length=settings.SEGMENT_CONDITION_VALUE_LIMIT, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_with_segment', models.BooleanField(default=False, help_text='Field to denote whether a condition was created along with segment or added after creation.')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('master_api_key', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='api_keys.masterapikey')),
                ('rule', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='segments.segmentrule')),
            ],
            options={
                'verbose_name': 'historical condition',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
