from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from features.feature_types import FEATURE_TYPE_CHOICES, MULTIVARIATE, STANDARD


def fix_feature_type(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    Feature = apps.get_model("features", "Feature")
    # Features with multivariate options should be MULTIVARIATE.
    Feature.objects.filter(multivariate_options__isnull=False).exclude(
        type=MULTIVARIATE
    ).update(type=MULTIVARIATE)
    # All remaining features with an invalid type should be STANDARD.
    Feature.objects.exclude(type__in=[STANDARD, MULTIVARIATE]).update(type=STANDARD)


class Migration(migrations.Migration):
    dependencies = [
        ("features", "0065_make_feature_value_size_configurable"),
        ("multivariate", "0007_alter_boolean_values"),
    ]

    operations = [
        migrations.RunPython(fix_feature_type, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="feature",
            name="type",
            field=models.CharField(
                blank=True,
                choices=FEATURE_TYPE_CHOICES,
                default=STANDARD,
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="historicalfeature",
            name="type",
            field=models.CharField(
                blank=True,
                choices=FEATURE_TYPE_CHOICES,
                default=STANDARD,
                max_length=50,
            ),
        ),
    ]
