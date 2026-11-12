from django.apps.registry import Apps
from django.db import migrations, models
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.models import Count

from core.migration_helpers import PostgresOnlyRunSQL


def deduplicate_system_tags(
    apps: Apps,
    schema_editor: BaseDatabaseSchemaEditor,
) -> None:
    Tag = apps.get_model("tags", "Tag")
    FeatureTag = apps.get_model("features", "Feature").tags.through

    # Block concurrent writes until the transaction commits, so no duplicate
    # can be inserted between this cleanup and the constraint creation below.
    # Reads are unaffected. Downstream forks may run other database vendors,
    # where the partial unique constraint is not supported and not created,
    # so the lock is only taken where the constraint exists to protect.
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "LOCK TABLE %s IN EXCLUSIVE MODE"
            % schema_editor.quote_name(Tag._meta.db_table)
        )

    duplicate_groups = (
        Tag.objects.filter(is_system_tag=True)
        .values("project_id", "label", "type")
        .annotate(count=Count("id"))
        .filter(count__gt=1)
    )
    for group in duplicate_groups:
        canonical_id, *duplicate_ids = (
            Tag.objects.filter(
                is_system_tag=True,
                project_id=group["project_id"],
                label=group["label"],
                type=group["type"],
            )
            .order_by("id")
            .values_list("id", flat=True)
        )
        # Re-point features tagged with a duplicate to the canonical tag,
        # skipping features already tagged with it to avoid violating the
        # M2M (feature, tag) uniqueness.
        feature_ids = set(
            FeatureTag.objects.filter(tag_id__in=duplicate_ids).values_list(
                "feature_id", flat=True
            )
        )
        already_tagged_feature_ids = set(
            FeatureTag.objects.filter(
                tag_id=canonical_id,
                feature_id__in=feature_ids,
            ).values_list("feature_id", flat=True)
        )
        FeatureTag.objects.bulk_create(
            FeatureTag(feature_id=feature_id, tag_id=canonical_id)
            for feature_id in feature_ids - already_tagged_feature_ids
        )
        Tag.objects.filter(id__in=duplicate_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tags", "0009_add_gitlab_tag_type"),
        ("features", "0023_auto_20200717_1515"),
    ]

    operations = [
        migrations.RunPython(
            deduplicate_system_tags,
            reverse_code=migrations.RunPython.noop,
        ),
        # Fire the deferred foreign key triggers queued by the deletes above,
        # so the unique index can be created in the same transaction.
        PostgresOnlyRunSQL(
            sql="SET CONSTRAINTS ALL IMMEDIATE",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AddConstraint(
            model_name="tag",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_system_tag", True)),
                fields=("project", "label", "type"),
                name="unique_project_label_type_system_tag",
            ),
        ),
    ]
