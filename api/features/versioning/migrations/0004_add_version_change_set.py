# Generated by Django 3.2.25 on 2024-07-10 11:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_lifecycle.mixins  # type: ignore[import-untyped]


class Migration(migrations.Migration):

    dependencies = [
        ('environments', '0034_alter_environment_project'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('workflows_core', '0009_prevent_cascade_delete_from_user_delete'),
        ('features', '0064_fix_feature_help_text_typo'),
        ('feature_versioning', '0003_cascade_delete_versions_on_cr_delete'),
    ]

    operations = [
        migrations.CreateModel(
            name='VersionChangeSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('live_from', models.DateTimeField(null=True)),
                ('feature_states_to_create', models.TextField(help_text='JSON blob describing the feature states that should be created when the change request is published', null=True)),
                ('feature_states_to_update', models.TextField(help_text='JSON blob describing the feature states that should be updated when the change request is published', null=True)),
                ('segment_ids_to_delete_overrides', models.TextField(help_text='JSON blob describing the segment overrides for whichthe segment overrides should be deleted when the change request is published', null=True)),
                ('change_request', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='change_sets', to='workflows_core.changerequest')),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='environments.environment')),
                ('environment_feature_version', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='feature_versioning.environmentfeatureversion')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='features.feature')),
                ('published_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'permissions': (('can_undelete', 'Can undelete this object'),),
                'abstract': False,
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
        ),
    ]
