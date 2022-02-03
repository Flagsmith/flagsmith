import typing

from core.constants import STRING


def test_remove_duplicate_mv_feature_state_values(migrator):
    # Given
    # We set the DB to be in the state prior to the migration we want to test
    old_state = migrator.apply_initial_migration(("multivariate", "0001_initial"))
    mv_feature_state_value_model = old_state.apps.get_model(
        "multivariate", "MultivariateFeatureStateValue"
    )
    mv_feature_option_model = old_state.apps.get_model(
        "multivariate", "MultivariateFeatureOption"
    )

    # and we set up some test data
    *_, feature, feature_state = _setup(old_state)

    # and we create 2 duplicate mv feature state value objects
    mv_feature_option_1 = mv_feature_option_model.objects.create(
        feature=feature,
        default_percentage_allocation=20,
        type=STRING,
        string_value="variant-1",
    )
    mv_feature_state_value_model.objects.create(
        feature_state=feature_state,
        multivariate_feature_option=mv_feature_option_1,
        percentage_allocation=20,
    )
    mv_feature_state_value_model.objects.create(
        feature_state=feature_state,
        multivariate_feature_option=mv_feature_option_1,
        percentage_allocation=20,
    )

    # and another non-duplicated feature state value object
    mv_feature_option_2 = mv_feature_option_model.objects.create(
        feature=feature,
        default_percentage_allocation=20,
        type=STRING,
        string_value="variant-2",
    )
    mv_feature_state_value_model.objects.create(
        feature_state=feature_state,
        multivariate_feature_option=mv_feature_option_2,
        percentage_allocation=20,
    )

    # When
    # We apply the new migration
    new_state = migrator.apply_tested_migration(
        ("multivariate", "0002_add_unique_constraint_for_mv_feature_states")
    )

    # and get the new model class
    mv_feature_state_value_model = new_state.apps.get_model(
        "multivariate", "MultivariateFeatureStateValue"
    )

    # Then
    # only 2 mv feature state value objects remain
    assert mv_feature_state_value_model.objects.count() == 2

    # only one of the duplicate mv feature state value models exists
    assert (
        mv_feature_state_value_model.objects.filter(
            multivariate_feature_option__id=mv_feature_option_1.id
        ).count()
        == 1
    )

    # and the other mv feature state value also still exists
    assert (
        mv_feature_state_value_model.objects.filter(
            multivariate_feature_option__id=mv_feature_option_2.id
        ).count()
        == 1
    )


def _setup(db_state) -> typing.Tuple:
    """Create some test data from a given db state"""
    organisation_model = db_state.apps.get_model("organisations", "Organisation")
    project_model = db_state.apps.get_model("projects", "Project")
    feature_model = db_state.apps.get_model("features", "Feature")
    environment_model = db_state.apps.get_model("environments", "Environment")
    feature_state_model = db_state.apps.get_model("features", "FeatureState")

    organisation = organisation_model.objects.create(name="Test org")
    project = project_model.objects.create(
        name="Test project", organisation=organisation
    )
    environment = environment_model.objects.create(
        name="Test Environment", project=project
    )
    feature = feature_model.objects.create(name="test_feature", project=project)
    feature_state = feature_state_model.objects.create(
        feature=feature, environment=environment
    )

    return organisation, project, environment, feature, feature_state
