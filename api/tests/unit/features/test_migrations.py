from datetime import timedelta

from django.utils import timezone

from features.feature_types import MULTIVARIATE, STANDARD


def test_migrate_feature_segments_forward(migrator):  # type: ignore[no-untyped-def]
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


def test_migrate_feature_segments_reverse(migrator):  # type: ignore[no-untyped-def]
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


def test_revert_feature_state_versioning_migrations(migrator):  # type: ignore[no-untyped-def]
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


def test_fix_feature_type_migration(migrator):  # type: ignore[no-untyped-def]
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


def test_migrate_sample_to_webhook_forward(migrator):  # type: ignore[no-untyped-def]
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_health", "0002_featurehealthevent_add_external_id_alter_created_at")
    )

    FeatureHealthProvider = old_state.apps.get_model(
        "feature_health", "FeatureHealthProvider"
    )
    FeatureHealthEvent = old_state.apps.get_model(
        "feature_health", "FeatureHealthEvent"
    )
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    feature = Feature.objects.create(name="test_feature", project=project)

    provider = FeatureHealthProvider.objects.create(name="Sample", project=project)
    event = FeatureHealthEvent.objects.create(
        feature=feature, type="UNHEALTHY", provider_name="Sample"
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_health", "0003_migrate_sample_to_webhook")
    )

    NewFeatureHealthProvider = new_state.apps.get_model(
        "feature_health", "FeatureHealthProvider"
    )
    NewFeatureHealthEvent = new_state.apps.get_model(
        "feature_health", "FeatureHealthEvent"
    )

    # Then
    assert NewFeatureHealthProvider.objects.get(id=provider.id).name == "Webhook"
    assert NewFeatureHealthEvent.objects.get(id=event.id).provider_name == "Webhook"
    assert not NewFeatureHealthProvider.objects.filter(name="Sample").exists()
    assert not NewFeatureHealthEvent.objects.filter(provider_name="Sample").exists()


def test_migrate_sample_to_webhook_reverse(migrator):  # type: ignore[no-untyped-def]
    # Given
    old_state = migrator.apply_initial_migration(
        ("feature_health", "0003_migrate_sample_to_webhook")
    )

    FeatureHealthProvider = old_state.apps.get_model(
        "feature_health", "FeatureHealthProvider"
    )
    FeatureHealthEvent = old_state.apps.get_model(
        "feature_health", "FeatureHealthEvent"
    )
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Feature = old_state.apps.get_model("features", "Feature")

    organisation = Organisation.objects.create(name="Test Org")
    project = Project.objects.create(name="Test Project", organisation=organisation)
    feature = Feature.objects.create(name="test_feature_webhook", project=project)

    provider = FeatureHealthProvider.objects.create(name="Webhook", project=project)
    event = FeatureHealthEvent.objects.create(
        feature_id=feature.id, type="UNHEALTHY", provider_name="Webhook"
    )

    # When
    new_state = migrator.apply_tested_migration(
        ("feature_health", "0002_featurehealthevent_add_external_id_alter_created_at")
    )

    NewFeatureHealthProvider = new_state.apps.get_model(
        "feature_health", "FeatureHealthProvider"
    )
    NewFeatureHealthEvent = new_state.apps.get_model(
        "feature_health", "FeatureHealthEvent"
    )

    # Then
    assert NewFeatureHealthProvider.objects.get(id=provider.id).name == "Sample"
    assert NewFeatureHealthEvent.objects.get(id=event.id).provider_name == "Sample"
    assert not NewFeatureHealthProvider.objects.filter(name="Webhook").exists()
    assert not NewFeatureHealthEvent.objects.filter(provider_name="Webhook").exists()
