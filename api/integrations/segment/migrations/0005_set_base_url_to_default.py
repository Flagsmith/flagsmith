from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from integrations.segment import constants


def set_base_url(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    SegmentConfiguration = apps.get_model("segment", "SegmentConfiguration")
    SegmentConfiguration.objects.filter(base_url__isnull=True).update(
        base_url=constants.DEFAULT_BASE_URL,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("segment", "0004_segmentconfiguration_deleted_at"),
    ]

    operations = [
        migrations.RunPython(set_base_url, reverse_code=migrations.RunPython.noop),
    ]
