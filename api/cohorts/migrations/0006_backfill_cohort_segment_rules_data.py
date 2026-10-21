from django.apps.registry import Apps
from django.db import migrations
from django.db.backends.base.schema import BaseDatabaseSchemaEditor

# Frozen copies of `cohorts.constants.COHORT_SYSTEM_TRAIT_KEY_PREFIX` and
# the segment constants, so that later changes don't alter this migration.
COHORT_SYSTEM_TRAIT_KEY_PREFIX = "flagsmith_cohort_"
ALL_RULE = "ALL"
IS_SET = "IS_SET"

BATCH_SIZE = 500


def backfill_cohort_segment_rules_data(
    apps: Apps, _: BaseDatabaseSchemaEditor | None = None
) -> None:
    """Populate `rules_data` on segments managed by live cohorts.

    Cohort segments created after `segments.0032_add_segment_rules_data`
    only earned row-based rules and conditions.
    """
    Cohort = apps.get_model("cohorts", "Cohort")
    Segment = apps.get_model("segments", "Segment")

    cohorts = (
        Cohort.objects.filter(
            deleted_at__isnull=True,
            segment__deleted_at__isnull=True,
            segment__rules_data__isnull=True,
        )
        .select_related("segment")
        .only("uuid", "segment__id", "segment__rules_data")
    )

    segments = []
    for cohort in cohorts.iterator(chunk_size=BATCH_SIZE):
        segment = cohort.segment
        segment.rules_data = [
            {
                "type": ALL_RULE,
                "conditions": [
                    {
                        "property": f"{COHORT_SYSTEM_TRAIT_KEY_PREFIX}{cohort.uuid}",
                        "operator": IS_SET,
                        "value": None,
                        "description": None,
                    }
                ],
            }
        ]
        segments.append(segment)

    Segment.objects.bulk_update(segments, fields=["rules_data"], batch_size=BATCH_SIZE)


class Migration(migrations.Migration):
    dependencies = [
        ("cohorts", "0005_cohort_last_synced_at"),
        ("segments", "0032_add_segment_rules_data"),
    ]

    operations = [
        migrations.RunPython(
            code=backfill_cohort_segment_rules_data,
            # Reversing leaves valid `rules_data` in place.
            reverse_code=migrations.RunPython.noop,
        ),
    ]
