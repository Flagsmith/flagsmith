from datetime import timedelta
import pytest
from django.utils import timezone
from django_test_migrations.migrator import Migrator
from django.conf import settings as test_settings


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_fix_scheduled_fs_data_issue_caused_by_enabling_versioning(
    migrator: Migrator,
) -> None:
    # Given
    now = timezone.now()
    one_hour_from_now = now + timedelta(hours=1)

    initial_state = migrator.apply_initial_migration(
        ("feature_versioning", "0004_add_version_change_set")
    )

    organisation_model_class = initial_state.apps.get_model(
        "organisations", "Organisation"
    )
    project_model_class = initial_state.apps.get_model("projects", "Project")
    environment_model_class = initial_state.apps.get_model(
        "environments", "Environment"
    )
    change_request_model_class = initial_state.apps.get_model(
        "workflows_core", "ChangeRequest"
    )
    environment_feature_version_model_class = initial_state.apps.get_model(
        "feature_versioning", "EnvironmentFeatureVersion"
    )
    feature_state_model_class = initial_state.apps.get_model("features", "FeatureState")
    feature_model_class = initial_state.apps.get_model("features", "Feature")

    organisation = organisation_model_class.objects.create(name="Test Organisation")
    project = project_model_class.objects.create(
        name="Test Project", organisation=organisation
    )
    environment_1 = environment_model_class.objects.create(
        name="Environment 1", project=project
    )
    feature = feature_model_class.objects.create(name="test_feature", project=project)

    # First, let's create some regular data that should be left untouched for a
    # non-versioned environment
    # Note: because migrations don't trigger the signals, we need to manually create
    # the default state
    environment_1_default_feature_state = feature_state_model_class.objects.create(
        feature=feature,
        environment=environment_1,
        version=1,
    )
    environment_1_live_cr = change_request_model_class.objects.create(
        title="Live CR for Environment 1",
        environment=environment_1,
    )
    environment_1_live_feature_state = feature_state_model_class.objects.create(
        feature=feature,
        environment=environment_1,
        enabled=True,
        live_from=one_hour_from_now,
        version=2,
        change_request=environment_1_live_cr,
    )

    # ... and a versioned environment
    versioned_environment = environment_model_class.objects.create(
        name="Versioned Environment",
        project=project,
        use_v2_feature_versioning=True,
    )
    versioned_environment_version_1 = (
        environment_feature_version_model_class.objects.create(
            feature=feature,
            environment=versioned_environment,
        )
    )
    versioned_environment_default_feature_state = (
        feature_state_model_class.objects.create(
            feature=feature,
            environment=versioned_environment,
            environment_feature_version=versioned_environment_version_1,
        )
    )
    versioned_environment_cr = change_request_model_class.objects.create(
        environment=versioned_environment,
        title="Versioned Environment CR",
    )
    versioned_environment_cr_version = (
        environment_feature_version_model_class.objects.create(
            feature=feature,
            environment=versioned_environment,
            change_request=versioned_environment_cr,
        )
    )
    versioned_environment_change_request_feature_state = (
        feature_state_model_class.objects.create(
            feature=feature,
            environment=versioned_environment,
            environment_feature_version=versioned_environment_cr_version,
        )
    )

    # Now, let's create the corrupt data that we want to correct
    environment_2 = environment_model_class.objects.create(
        name="Environment 2", project=project
    )
    # Note: because migrations don't trigger the signals, we need to manually create
    # the default state
    feature_state_model_class.objects.create(
        feature=feature,
        environment=environment_2,
        version=1,
    )
    environment_2_scheduled_cr = change_request_model_class.objects.create(
        title="Environment 2 Scheduled CR",
        environment=environment_2,
    )
    environment_2_scheduled_feature_state = feature_state_model_class.objects.create(
        feature=feature,
        environment=environment_2,
        live_from=one_hour_from_now,
        version=2,
        change_request=environment_2_scheduled_cr,
    )

    # and let's explicitly write out the corruption steps as they would have occurred
    # when any environment has feature versioning enabled.
    # 1. The scheduled feature state for environment 2 would be associated with a new
    #    environment feature version in that environment.
    new_version = environment_feature_version_model_class.objects.create(
        environment=versioned_environment,
        feature=feature,
    )
    environment_2_scheduled_feature_state.environment_feature_version = new_version

    # 2. The change request would be removed from the feature state
    environment_2_scheduled_feature_state.change_request = None

    # 3. The change request would be added to the new version instead
    new_version.change_request = environment_2_scheduled_cr

    # 4. Let's save the models with the modifications
    new_version.save()
    environment_2_scheduled_feature_state.save()

    # When
    new_state = migrator.apply_tested_migration(
        (
            "feature_versioning",
            "0005_fix_scheduled_fs_data_issue_caused_by_enabling_versioning",
        )
    )

    # Then
    feature_state_model_class = new_state.apps.get_model("features", "FeatureState")

    # Let's check that the regular data is untouched
    assert (
        feature_state_model_class.objects.get(
            pk=environment_1_default_feature_state.pk
        ).environment_feature_version
        is None
    )
    assert (
        feature_state_model_class.objects.get(
            pk=environment_1_live_feature_state.pk
        ).environment_feature_version
        is None
    )
    assert (
        feature_state_model_class.objects.get(
            pk=versioned_environment_default_feature_state.pk
        ).environment_feature_version_id
        == versioned_environment_version_1.pk
    )
    assert (
        feature_state_model_class.objects.get(
            pk=versioned_environment_change_request_feature_state.pk
        ).environment_feature_version_id
        == versioned_environment_cr_version.pk
    )

    # And let's check the corrupted data issue has been solved
    new_environment_2_scheduled_feature_state = feature_state_model_class.objects.get(
        pk=environment_2_scheduled_feature_state.pk
    )
    assert new_environment_2_scheduled_feature_state.environment_feature_version is None
    assert (
        new_environment_2_scheduled_feature_state.change_request_id
        == environment_2_scheduled_cr.pk
    )
