# TODO: squash 0005 and this migration together

from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

from integrations.segment import constants

_INVALID_DEFAULT_BASE_URL = "api.segment.io/"


def set_base_url(apps: Apps, schema_editor: BaseDatabaseSchemaEditor) -> None:
    SegmentConfiguration = apps.get_model("segment", "SegmentConfiguration")
    SegmentConfiguration.objects.filter(base_url=_INVALID_DEFAULT_BASE_URL).update(
        base_url=constants.DEFAULT_BASE_URL,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("segment", "0005_set_base_url_to_default"),
    ]

    operations = [
        migrations.RunPython(set_base_url, reverse_code=migrations.RunPython.noop),
    ]
