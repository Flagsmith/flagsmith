from django.utils import timezone
from django_test_migrations.migrator import Migrator


def test_0006_backfill_cohort_segment_rules_data__cohort_segments__backfills_live_ones_only(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(
        ("cohorts", "0005_cohort_last_synced_at")
    )
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Environment = old_state.apps.get_model("environments", "Environment")
    Segment = old_state.apps.get_model("segments", "Segment")
    Cohort = old_state.apps.get_model("cohorts", "Cohort")

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    environment = Environment.objects.create(name="Test Environment", project=project)

    def create_cohort_segment(name: str, **cohort_kwargs: object) -> tuple[int, str]:
        segment = Segment.objects.create(
            name=name, project=project, managed_by="cohort"
        )
        cohort = Cohort.objects.create(
            environment=environment, segment=segment, **cohort_kwargs
        )
        return segment.id, str(cohort.uuid)

    live_segment_id, live_cohort_uuid = create_cohort_segment("Live")
    deleted_cohort_segment_id, _ = create_cohort_segment(
        "Deleted cohort", deleted_at=timezone.now()
    )
    deleted_segment_id, _ = create_cohort_segment("Deleted segment")
    Segment.objects.filter(id=deleted_segment_id).update(deleted_at=timezone.now())
    existing_rules_data = [{"type": "ANY", "conditions": []}]
    populated_segment_id, _ = create_cohort_segment("Populated")
    Segment.objects.filter(id=populated_segment_id).update(
        rules_data=existing_rules_data
    )
    unmanaged_segment = Segment.objects.create(name="Unmanaged", project=project)

    # When
    new_state = migrator.apply_tested_migration(
        ("cohorts", "0006_backfill_cohort_segment_rules_data")
    )

    # Then
    NewSegment = new_state.apps.get_model("segments", "Segment")
    assert NewSegment.objects.get(id=live_segment_id).rules_data == [
        {
            "type": "ALL",
            "conditions": [
                {
                    "property": f"flagsmith_cohort_{live_cohort_uuid}",
                    "operator": "IS_SET",
                    "value": None,
                    "description": None,
                }
            ],
        }
    ]
    assert NewSegment.objects.get(id=deleted_cohort_segment_id).rules_data is None
    assert NewSegment.objects.get(id=deleted_segment_id).rules_data is None
    assert (
        NewSegment.objects.get(id=populated_segment_id).rules_data
        == existing_rules_data
    )
    assert NewSegment.objects.get(id=unmanaged_segment.id).rules_data is None
