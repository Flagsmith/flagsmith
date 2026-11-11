from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("audit", "0016_add_organisation_id"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="auditlog",
            index=models.Index(fields=["organisation"], name="audit_organisation_idx"),
        ),
    ]
