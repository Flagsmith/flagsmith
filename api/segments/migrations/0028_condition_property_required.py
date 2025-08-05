from collections.abc import Callable
from typing import Any

from django.apps.registry import Apps
from django.db import migrations, models


def fill_percentage_split_property_for(model_name: str) -> Callable[[Apps, Any], None]:
    def fill_property(apps: Apps, _: Any) -> None:
        model = apps.get_model("segments", model_name)
        model.objects.filter(
            models.Q(operator="PERCENTAGE_SPLIT") & (
                models.Q(property__isnull=True) | models.Q(property__regex=r"^\s*$")
            )
        ).update(property="$.identity.key")

    return fill_property


def reverse_fill_percentage_split_property_for(model_name: str) -> Callable[[Apps, Any], None]:
    def reverse_fill_property(apps: Apps, _: Any) -> None:
        model = apps.get_model("segments", model_name)
        model.objects.filter(
            operator="PERCENTAGE_SPLIT", property="$.identity.key"
        ).update(property=None)

    return reverse_fill_property


class Migration(migrations.Migration):
    """
    Update condition.property to be non-nullable.

    Only conditions of operator PERCENTAGE_SPLIT have empty `property` values,
    according to this query:

    ```sql
    select c.operator, count(*) from segments_condition c where c.property is null or c.property !~ '\\S' group by 1;
    ```

    The Flagsmith engine can now do percentage split upon any property, so we
    default empty `property` values to `"$.identity.key"` because that's the
    old behavior for PERCENTAGE_SPLIT conditions.
    """

    dependencies = [
        ("segments", "0027_historicalsegmentrule"),
    ]

    operations = [
        migrations.AlterField(
            model_name="condition",
            name="property",
            field=models.CharField(max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name="historicalcondition",
            name="property",
            field=models.CharField(max_length=1000, null=True),
        ),
        migrations.RunPython(
            code=fill_percentage_split_property_for("Condition"),
            reverse_code=reverse_fill_percentage_split_property_for("Condition"),
        ),
        migrations.RunPython(
            code=fill_percentage_split_property_for("HistoricalCondition"),
            reverse_code=reverse_fill_percentage_split_property_for("HistoricalCondition"),
        ),
    ]
