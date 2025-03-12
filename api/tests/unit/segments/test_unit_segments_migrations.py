import uuid

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


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_add_versioning_to_segments_forwards(migrator: Migrator) -> None:
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
def test_add_versioning_to_segments_reverse(migrator: Migrator) -> None:
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
