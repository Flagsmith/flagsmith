from django.apps.registry import Apps
from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def backfill_feature_names(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    FeatureFlagCodeReferencesScan = apps.get_model(
        "code_references", "FeatureFlagCodeReferencesScan"
    )
    scans = list(FeatureFlagCodeReferencesScan.objects.all())
    for scan in scans:
        scan.feature_names = sorted(
            {ref["feature_name"] for ref in scan.code_references}
        )
    FeatureFlagCodeReferencesScan.objects.bulk_update(scans, ["feature_names"])


class Migration(migrations.Migration):

    dependencies = [
        ("code_references", "0002_add_project_repo_created_index"),
    ]

    operations = [
        migrations.AddField(
            model_name="featureflagcodereferencesscan",
            field=ArrayField(models.TextField(), default=list),
            name="feature_names",
        ),
        migrations.RunPython(
            backfill_feature_names,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
