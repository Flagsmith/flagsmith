from datetime import timedelta

from django.utils import timezone


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


def test_revert_feature_state_versioning_migrations(migrator):
    # Given
    old_state = migrator.apply_initial_migration(
        ("features", "0039_add_new_unique_indexes")
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
        live_from=timezone.now() - timedelta(days=1),
    )
    v2 = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=2,
        live_from=timezone.now() - timedelta(days=1),
    )
    v3 = FeatureState.objects.create(
        environment=environment,
        feature=feature,
        version=3,
        live_from=timezone.now() + timedelta(days=1),
    )

    # When
    new_state = migrator.apply_tested_migration(("features", "0035_auto_20211109_0603"))

    # Then
    # only the latest live versions of feature states are retained
    NewFeatureState = new_state.apps.get_model("features", "FeatureState")
    assert not NewFeatureState.objects.filter(id=v1.id).exists()
    assert not NewFeatureState.objects.filter(id=v3.id).exists()
    assert NewFeatureState.objects.filter(id=v2.id).exists()
