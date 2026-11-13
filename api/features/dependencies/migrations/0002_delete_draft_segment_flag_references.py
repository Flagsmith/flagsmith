from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor


def delete_draft_segment_flag_references(
    apps: Apps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    segment_flag_reference_model = apps.get_model(
        "feature_dependencies", "SegmentFlagReference"
    )
    segment_flag_reference_model.objects.filter(
        segment__change_request__isnull=False
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("feature_dependencies", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            delete_draft_segment_flag_references,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
