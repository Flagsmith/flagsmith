from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from features.feature_types import MULTIVARIATE, STANDARD

now = timezone.now()
one_hour_ago = now - timedelta(hours=1)
two_hours_ago = now - timedelta(hours=2)
yesterday = now - timedelta(days=1)


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_migrate_feature_segments_forward(migrator):
    # Given - the migration state is at 0017 (before the migration we want to test)
    old_state = migrator.apply_initial_migration(
        ("features", "0017_auto_20200607_1005")
    )
    OldFeatureSegment = old_state.apps.get_model("features", "FeatureSegment")
    OldFeatureState = old_state.apps.get_model("features", "FeatureState")

    # use the migration state to get the classes we need for test data
    Feature = old_state.apps.get_model("features", "Feature")
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Segment = old_state.apps.get_model("segments", "Segment")
    Environment = old_state.apps.get_model("environments", "Environment")

    # setup some test data
    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    feature = Feature.objects.create(name="Test feature", project=project)
    segment_1 = Segment.objects.create(name="Test segment 1", project=project)
    segment_2 = Segment.objects.create(name="Test segment 2", project=project)
    environment_1 = Environment.objects.create(
        name="Test environment 1", project=project
    )
    environment_2 = Environment.objects.create(
        name="Test environment 2", project=project
    )

    # create 2 feature segment without an environment and with enabled overridden to true
    feature_segment_1 = OldFeatureSegment.objects.create(
        feature=feature, segment=segment_1, enabled=True, priority=0
    )
    feature_segment_2 = OldFeatureSegment.objects.create(
        feature=feature, segment=segment_2, enabled=True, priority=1
    )

    # mimick the creation of the feature states that would have happened when save is called on the model (but doesn't
    # happen because we're using the migrator models)
    OldFeatureState.objects.create(
        feature=feature, environment=environment_1, feature_segment=feature_segment_1
    )
    OldFeatureState.objects.create(
        feature=feature, environment=environment_2, feature_segment=feature_segment_1
    )
    OldFeatureState.objects.create(
        feature=feature, environment=environment_1, feature_segment=feature_segment_2
    )
    OldFeatureState.objects.create(
        feature=feature, environment=environment_2, feature_segment=feature_segment_2
    )

    # When
    new_state = migrator.apply_tested_migration(("features", "0018_auto_20200607_1057"))
    NewFeatureSegment = new_state.apps.get_model("features", "FeatureSegment")
    NewFeatureState = new_state.apps.get_model("features", "FeatureState")

    # Then - there are 4 feature segments, for each feature segment, create 1 for each environment
    assert NewFeatureSegment.objects.count() == 4
    assert NewFeatureSegment.objects.filter(
        segment_id=segment_1.id, environment__pk=environment_1.pk, enabled=True
    ).exists()
    assert NewFeatureSegment.objects.filter(
        segment_id=segment_1.id, environment__pk=environment_2.pk, enabled=True
    ).exists()
    assert NewFeatureSegment.objects.filter(
        segment_id=segment_2.id, environment__pk=environment_1.pk, enabled=True
    ).exists()
    assert NewFeatureSegment.objects.filter(
        segment_id=segment_2.id, environment__pk=environment_2.pk, enabled=True
    ).exists()
    assert not NewFeatureSegment.objects.filter(environment__isnull=True).exists()

    # verify that the feature states are created / updated with the new feature segments
    assert NewFeatureState.objects.values("feature_segment").distinct().count() == 4


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_migrate_feature_segments_reverse(migrator):
    # Given - migration state is at 0018, after the migration we want to test in reverse
    old_state = migrator.apply_initial_migration(
        ("features", "0018_auto_20200607_1057")
    )
    OldFeatureSegment = old_state.apps.get_model("features", "FeatureSegment")

    # use the migration state to get the classes we need for test data
    Feature = old_state.apps.get_model("features", "Feature")
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Segment = old_state.apps.get_model("segments", "Segment")
    Environment = old_state.apps.get_model("environments", "Environment")

    # setup some test data
    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test project", organisation=organisation)
    feature = Feature.objects.create(name="Test feature", project=project)
    segment = Segment.objects.create(name="Test segment", project=project)
    environment_1 = Environment.objects.create(
        name="Test environment 1", project=project
    )
    environment_2 = Environment.objects.create(
        name="Test environment 2", project=project
    )

    # create a feature segment for each environment
    OldFeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_1,
        enabled=True,
        priority=0,
    )
    OldFeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_2,
        enabled=False,
        priority=0,
    )

    # When
    new_state = migrator.apply_tested_migration(("features", "0017_auto_20200607_1005"))
    NewFeatureSegment = new_state.apps.get_model("features", "FeatureSegment")

    # Then - there is only one feature segment left
    assert NewFeatureSegment.objects.count() == 1
    # Note that it's not possible to determine which feature segment to keep so we can't test that it keeps the
    # correct value. Just verify that the essential data is the same.
    assert NewFeatureSegment.objects.first().feature.pk == feature.pk
    assert NewFeatureSegment.objects.first().segment.pk == segment.pk


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_revert_feature_state_versioning_migrations(migrator):
    # Given
    old_state = migrator.apply_initial_migration(
        ("features", "0038_remove_old_versions_and_drafts")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Environment = old_state.apps.get_model("environments", "Environment")
    Feature = old_state.apps.get_model("features", "Feature")
    FeatureState = old_state.apps.get_model("features", "FeatureState")

    organisation = Organisation.objects.create(name="test org")
    project = Project.objects.create(name="test project", organisation=organisation)
    environment = Environment.objects.create(name="test environment", project=project)
    feature = Feature.objects.create(name="test_feature", project=project)

    v1 = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=1,
        live_from=yesterday,
    )
    v2 = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=2,
        live_from=yesterday,
    )
    v3 = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=3,
        live_from=yesterday,
    )

    # When
    new_state = migrator.apply_tested_migration(("features", "0035_auto_20211109_0603"))

    # Then
    # only the latest live versions of feature states are retained
    NewFeatureState = new_state.apps.get_model("features", "FeatureState")
    assert not NewFeatureState.objects.filter(id=v1.id).exists()
    assert not NewFeatureState.objects.filter(id=v3.id).exists()
    assert NewFeatureState.objects.filter(id=v2.id).exists()


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_fix_feature_type_migration(migrator):
    # Given
    old_state = migrator.apply_initial_migration(
        ("features", "0058_alter_boolean_values")
    )

    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")
    MultivariateFeatureOption = old_state.apps.get_model(
        "multivariate", "MultivariateFeatureOption"
    )

    organisation = Organisation.objects.create(name="test org")
    project = Project.objects.create(
        name="test project", organisation_id=organisation.id
    )
    standard_feature = Feature.objects.create(
        name="test_feature", project_id=project.id
    )
    mv_feature = Feature.objects.create(
        name="mv_feature", project_id=project.id, type=MULTIVARIATE
    )
    standard_feature_with_mv_option = Feature.objects.create(
        name="standard_feature_with_mv_option", project_id=project.id
    )
    MultivariateFeatureOption.objects.create(
        feature_id=standard_feature_with_mv_option.id
    )

    # When
    new_state = migrator.apply_tested_migration(("features", "0059_fix_feature_type"))

    # Then
    NewFeature = new_state.apps.get_model("features", "Feature")
    assert (
        NewFeature.objects.get(id=standard_feature_with_mv_option.id).type
        == MULTIVARIATE
    )
    assert NewFeature.objects.get(id=standard_feature.id).type == STANDARD
    assert NewFeature.objects.get(id=mv_feature.id).type == MULTIVARIATE


@pytest.mark.skipif(
    settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_remove_redundant_feature_segments(migrator):
    old_state = migrator.apply_initial_migration(("features", "0059_fix_feature_type"))

    # get all the model classes we need
    organisation_model = old_state.apps.get_model("organisations", "organisation")
    project_model = old_state.apps.get_model("projects", "project")
    environment_model = old_state.apps.get_model("environments", "environment")
    feature_model = old_state.apps.get_model("features", "feature")
    feature_state_model = old_state.apps.get_model("features", "featurestate")
    feature_segment_model = old_state.apps.get_model("features", "featuresegment")
    segment_model = old_state.apps.get_model("segments", "segment")

    # set up the scaffolding data
    organisation = organisation_model.objects.create(name="test")
    project = project_model.objects.create(name="test", organisation_id=organisation.id)
    environment = environment_model.objects.create(name="test", project_id=project.id)
    feature = feature_model.objects.create(name="test", project_id=project.id)
    segment_1 = segment_model.objects.create(name="test1", project_id=project.id)

    # create a feature segment with 2 feature states
    feature_segment_1 = feature_segment_model.objects.create(
        feature_id=feature.id, environment_id=environment.id, segment_id=segment_1.id, priority=1
    )
    feature_state_1 = feature_state_model.objects.create(
        feature_id=feature.id,
        environment_id=environment.id,
        feature_segment_id=feature_segment_1.id,
        version=1,
        live_from=one_hour_ago,
    )
    feature_state_2 = feature_state_model.objects.create(
        feature_id=feature.id,
        environment_id=environment.id,
        feature_segment_id=feature_segment_1.id,
        version=None,
        live_from=two_hours_ago,
    )
    feature_state_2.version = 1
    feature_state_2.save()

    # and one with a single feature state which shouldn't be affected
    segment_2 = segment_model.objects.create(name="test2", project_id=project.id)
    feature_segment_2 = feature_segment_model.objects.create(
        feature_id=feature.id,
        environment_id=environment.id,
        segment_id=segment_2.id,
        priority=1,
    )
    feature_state_3 = feature_state_model.objects.create(
        feature_id=feature.id,
        environment_id=environment.id,
        feature_segment_id=feature_segment_2.id,
        version=1,
        live_from=one_hour_ago,
    )

    # now let's run the migration
    new_state = migrator.apply_tested_migration(
        ("features", "0060_remove_redundant_segment_override_feature_states")
    )

    # and we should see that only one feature state is left for the feature segment that had
    # 2 feature states - the one with the most recent live from
    new_feature_segment_model = new_state.apps.get_model("features", "featuresegment")

    feature_segment_1_post_migration = new_feature_segment_model.objects.get(
        feature_id=feature.id, environment_id=environment.id, segment_id=segment_1.id
    )
    assert feature_segment_1_post_migration.feature_states.count() == 1
    assert (
        feature_segment_1_post_migration.feature_states.first().id == feature_state_1.id
    )

    # and the feature segment which only had one, still has it
    feature_segment_2_post_migration = new_feature_segment_model.objects.get(
        feature_id=feature.id, environment_id=environment.id, segment_id=segment_2.id
    )
    assert feature_segment_2_post_migration.feature_states.count() == 1
    assert feature_segment_2_post_migration.feature_states.first().id == feature_state_3.id
