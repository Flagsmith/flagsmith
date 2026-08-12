import uuid
from importlib import import_module

import pytest
from django.conf import settings as test_settings
from django.utils import timezone
from django_test_migrations.migrator import Migrator
from flag_engine.segments import constants
from pytest_django.fixtures import SettingsWrapper

migration_0032 = import_module("segments.migrations.0032_add_segment_rules_data")


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_create_whitelisted_segments_migration__segment_exceeds_limit__adds_to_whitelist(
    migrator: Migrator,
    settings: SettingsWrapper,
) -> None:
    # Given - The migration state is at 0020 (before the migration we want to test).
    old_state = migrator.apply_initial_migration(
        ("segments", "0020_detach_segment_from_project_cascade_delete")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    SegmentRule = old_state.apps.get_model("segments", "SegmentRule")
    Segment = old_state.apps.get_model("segments", "Segment")
    Condition = old_state.apps.get_model("segments", "Condition")

    # Set the limit lower to allow for a faster test.
    settings.SEGMENT_RULES_CONDITIONS_LIMIT = 3

    # Next, create the setup data.
    organisation = Organisation.objects.create(name="Big Corp Incorporated")
    project = Project.objects.create(name="Huge Project", organisation=organisation)

    segment_1 = Segment.objects.create(name="Segment1", project=project)
    segment_2 = Segment.objects.create(name="Segment1", project=project)
    segment_rule_1 = SegmentRule.objects.create(
        segment=segment_1,
        type="ALL",
    )

    # Subnested segment rules.
    segment_rule_2 = SegmentRule.objects.create(
        rule=segment_rule_1,
        type="ALL",
    )
    segment_rule_3 = SegmentRule.objects.create(
        rule=segment_rule_1,
        type="ALL",
    )

    # Lonely segment rules for pass criteria for segment_2.
    segment_rule_4 = SegmentRule.objects.create(
        segment=segment_2,
        type="ALL",
    )
    segment_rule_5 = SegmentRule.objects.create(
        rule=segment_rule_4,
        type="ALL",
    )

    Condition.objects.create(
        operator=constants.EQUAL,
        property="age",
        value="21",
        rule=segment_rule_2,
    )
    Condition.objects.create(
        operator=constants.GREATER_THAN,
        property="height",
        value="210",
        rule=segment_rule_2,
    )
    Condition.objects.create(
        operator=constants.GREATER_THAN,
        property="waist",
        value="36",
        rule=segment_rule_3,
    )
    Condition.objects.create(
        operator=constants.LESS_THAN,
        property="shoes",
        value="12",
        rule=segment_rule_3,
    )

    # Sole criteria for segment_2 conditions.
    Condition.objects.create(
        operator=constants.LESS_THAN,
        property="toy_count",
        value="7",
        rule=segment_rule_5,
    )

    # When we run the migration.
    new_state = migrator.apply_tested_migration(
        ("segments", "0021_create_whitelisted_segments")
    )

    # Then the first segment is in the whitelist while the second is not.
    NewSegment = new_state.apps.get_model("segments", "Segment")
    new_segment_1 = NewSegment.objects.get(id=segment_1.id)
    new_segment_2 = NewSegment.objects.get(id=segment_2.id)
    assert new_segment_1.whitelisted_segment
    assert getattr(new_segment_2, "whitelisted_segment", None) is None


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_add_versioning_to_segments__forwards__sets_version_of_to_self(
    migrator: Migrator,
) -> None:
    # Given - The migration state is at 0021 (before the migration we want to test).
    old_state = migrator.apply_initial_migration(
        ("segments", "0022_add_soft_delete_to_segment_rules_and_conditions")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    SegmentRule = old_state.apps.get_model("segments", "SegmentRule")
    Segment = old_state.apps.get_model("segments", "Segment")
    Condition = old_state.apps.get_model("segments", "Condition")

    # Next, create the setup data.
    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(
        name="Test Project", organisation_id=organisation.id
    )

    segment = Segment.objects.create(name="Segment1", project_id=project.id)
    segment_rule_1 = SegmentRule.objects.create(
        segment_id=segment.id,
        type="ALL",
    )

    # Subnested segment rules.
    segment_rule_2 = SegmentRule.objects.create(
        rule_id=segment_rule_1.id,
        type="ALL",
    )

    Condition.objects.create(
        operator=constants.EQUAL,
        property="age",
        value="21",
        rule_id=segment_rule_2.id,
    )

    # When we run the migration.
    new_state = migrator.apply_tested_migration(
        ("segments", "0023_add_versioning_to_segments")
    )

    # Then the version_of attribute is correctly set.
    NewSegment = new_state.apps.get_model("segments", "Segment")
    new_segment = NewSegment.objects.get(id=segment.id)
    assert new_segment.version_of == new_segment


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_add_versioning_to_segments__reverse__deletes_historical_versions(
    migrator: Migrator,
) -> None:
    # Given - The migration state is at 0023 (after the migration we want to test).
    old_state = migrator.apply_initial_migration(
        ("segments", "0023_add_versioning_to_segments")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    SegmentRule = old_state.apps.get_model("segments", "SegmentRule")
    Segment = old_state.apps.get_model("segments", "Segment")
    Condition = old_state.apps.get_model("segments", "Condition")

    # Next, create the setup data.
    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)

    # Set the version manually since this is normally done via a lifecycle hook
    # that doesn't run for models created in a migration state.
    segment = Segment.objects.create(name="Segment1", project=project, version=1)
    segment_rule_1 = SegmentRule.objects.create(
        segment=segment,
        type="ALL",
    )

    # We ideally want to call Segment.deep_clone but that's not
    # possible when working in a migration state. As such, we
    # do the basic amount necessary from that method to allow
    # us to test the migration behaviour.
    def _deep_clone(segment: Segment) -> Segment:  # type: ignore[valid-type]
        cloned_segment = Segment.objects.create(
            name=segment.name,  # type: ignore[attr-defined]
            project_id=segment.project_id,  # type: ignore[attr-defined]
            description=segment.description,  # type: ignore[attr-defined]
            feature=segment.feature,  # type: ignore[attr-defined]
            uuid=uuid.uuid4(),
            version_of_id=segment.id,  # type: ignore[attr-defined]
        )

        segment.version += 1  # type: ignore[attr-defined]
        segment.save()  # type: ignore[attr-defined]

        return cloned_segment  # type: ignore[no-any-return]

    version_1 = _deep_clone(segment)
    version_2 = _deep_clone(segment)

    version_3 = segment

    # Subnested segment rules.
    segment_rule_2 = SegmentRule.objects.create(
        rule=segment_rule_1,
        type="ALL",
    )

    Condition.objects.create(
        operator=constants.EQUAL,
        property="age",
        value="21",
        rule=segment_rule_2,
    )

    # When we run the migration in reverse.
    new_state = migrator.apply_tested_migration(
        ("segments", "0022_add_soft_delete_to_segment_rules_and_conditions")
    )

    # Then any historical versions of the segment are deleted.
    NewSegment = new_state.apps.get_model("segments", "Segment")

    new_segment_v1 = NewSegment.objects.get(id=version_1.id)  # type: ignore[attr-defined]
    assert new_segment_v1.deleted_at is not None

    new_segment_v2 = NewSegment.objects.get(id=version_2.id)  # type: ignore[attr-defined]
    assert new_segment_v2.deleted_at is not None

    new_segment_v3 = NewSegment.objects.get(id=version_3.id)
    assert new_segment_v3.deleted_at is None


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_0032_add_segment_rules_data__forwards__backfill_segment_rules_data(
    migrator: Migrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr(migration_0032, "BATCH_SIZE", 2)
    state = migrator.apply_initial_migration(
        ("segments", "0032_add_segment_rules_data")
    )

    Organisation = state.apps.get_model("organisations", "Organisation")
    Project = state.apps.get_model("projects", "Project")
    Segment = state.apps.get_model("segments", "Segment")
    SegmentRule = state.apps.get_model("segments", "SegmentRule")
    Condition = state.apps.get_model("segments", "Condition")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)

    segment = Segment.objects.create(name="Current", project=project)
    segment.version_of_id = segment.id
    segment.save()
    top_rule = SegmentRule.objects.create(segment=segment, type="ALL")
    nested_rule = SegmentRule.objects.create(rule=top_rule, type="ANY")
    deep_rule = SegmentRule.objects.create(rule=nested_rule, type="NONE")
    deleted_rule = SegmentRule.objects.create(
        rule=top_rule, type="ANY", deleted_at=timezone.now()
    )
    orphaned_rule = SegmentRule.objects.create(rule=deleted_rule, type="ANY")
    Condition.objects.create(
        rule=orphaned_rule,
        operator=constants.EQUAL,
        property="ghost",
        value="true",
    )
    Condition.objects.create(
        rule=top_rule,
        operator=constants.IS_SET,
        property="email",
        value="",
    )
    Condition.objects.create(
        rule=nested_rule,
        operator=constants.EQUAL,
        property="age",
        value="21",
        description="Adults only",
    )
    Condition.objects.create(
        rule=nested_rule,
        operator=constants.GREATER_THAN,
        property="height",
        value="210",
        deleted_at=timezone.now(),
    )
    Condition.objects.create(
        rule=deep_rule,
        operator=constants.CONTAINS,
        property="country",
        value="GB",
    )

    deleted_segment = Segment.objects.create(
        name="Deleted", project=project, deleted_at=timezone.now()
    )
    deleted_segment.version_of_id = deleted_segment.id
    deleted_segment.save()
    SegmentRule.objects.create(segment=deleted_segment, type="ALL")

    old_version_segment = Segment.objects.create(
        name="Old version", project=project, version_of_id=segment.id
    )
    SegmentRule.objects.create(segment=old_version_segment, type="ALL")

    empty_segment = Segment.objects.create(name="Empty", project=project)
    empty_segment.version_of_id = empty_segment.id
    empty_segment.save()

    batched_segments = []
    for i in range(3):  # spans several batches
        batched_segment = Segment.objects.create(name=f"Batched {i}", project=project)
        batched_segment.version_of_id = batched_segment.id
        batched_segment.save()
        rule = SegmentRule.objects.create(segment=batched_segment, type="ALL")
        Condition.objects.create(
            rule=rule,
            operator=constants.EQUAL,
            property="batch",
            value=str(i),
        )
        batched_segments.append(batched_segment)

    # When
    migration_0032.backfill_segment_rules_data(state.apps)

    # Then
    segment.refresh_from_db()
    deleted_segment.refresh_from_db()
    old_version_segment.refresh_from_db()
    assert segment.rules_data == [
        {
            "type": "ALL",
            "conditions": [
                {
                    "property": "email",
                    "operator": constants.IS_SET,
                    "value": "",
                    "description": None,
                }
            ],
            "rules": [
                {
                    "type": "ANY",
                    "conditions": [
                        {
                            "property": "age",
                            "operator": constants.EQUAL,
                            "value": "21",
                            "description": "Adults only",
                        }
                    ],
                    # Our UI never allowed more than two levels, but our API did
                    "rules": [
                        {
                            "type": "NONE",
                            "conditions": [
                                {
                                    "property": "country",
                                    "operator": constants.CONTAINS,
                                    "value": "GB",
                                    "description": None,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    ]
    assert deleted_segment.rules_data is None
    assert old_version_segment.rules_data is None

    empty_segment.refresh_from_db()
    assert empty_segment.rules_data == []

    for i, batched_segment in enumerate(batched_segments):
        batched_segment.refresh_from_db()
        assert batched_segment.rules_data == [
            {
                "type": "ALL",
                "conditions": [
                    {
                        "property": "batch",
                        "operator": constants.EQUAL,
                        "value": str(i),
                        "description": None,
                    }
                ],
                # NOTE: Empty rules are dropped at any level!
            }
        ]


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_0032_add_segment_rules_data__backwards__nullify_segment_rules_data(
    migrator: Migrator,
) -> None:
    # Given
    state = migrator.apply_initial_migration(
        ("segments", "0032_add_segment_rules_data")
    )

    Organisation = state.apps.get_model("organisations", "Organisation")
    Project = state.apps.get_model("projects", "Project")
    Segment = state.apps.get_model("segments", "Segment")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)

    backfilled_segment = Segment.objects.create(
        name="Backfilled",
        project=project,
        rules_data=[{"type": "ALL", "conditions": [], "rules": []}],
    )
    blank_segment = Segment.objects.create(name="Blank", project=project)

    # When
    migration_0032.nullify_segment_rules_data(state.apps)

    # Then
    backfilled_segment.refresh_from_db()
    blank_segment.refresh_from_db()
    assert backfilled_segment.rules_data is None
    assert blank_segment.rules_data is None
