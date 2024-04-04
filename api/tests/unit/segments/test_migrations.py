import pytest
from django.conf import settings as test_settings
from django_test_migrations.migrator import Migrator
from flag_engine.segments import constants
from pytest_django.fixtures import SettingsWrapper


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_create_whitelisted_segments_migration(
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
