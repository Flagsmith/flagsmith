from django.db import migrations, models
from django.db.models import Q


def add_default_base_url(apps, schema_editor):  # type: ignore[no-untyped-def]
    heap_configuration_model = apps.get_model("heap", "HeapConfiguration")

    heap_configuration_model.objects.filter(
        Q(base_url__isnull=True) | Q(base_url="")
    ).update(base_url="https://heapanalytics.com")


class Migration(migrations.Migration):
    dependencies = [
        ("heap", "0003_heapconfiguration_deleted_at"),
    ]

    operations = [
        migrations.RunPython(
            add_default_base_url, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="heapconfiguration",
            name="base_url",
            field=models.URLField(default="https://heapanalytics.com"),
        ),
    ]
