from features.models import FeatureSegment, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from segments.models import Segment


def test_create_new_environment_feature_version_clones_feature_states_from_previous_version(
    environment, feature
):
    # Given
    segment = Segment.objects.create(project=environment.project)
    feature_segment = FeatureSegment.objects.create(
        segment=segment, feature=feature, environment=environment
    )
    FeatureState.objects.create(
        environment=environment, feature=feature, feature_segment=feature_segment
    )

    environment.use_v2_feature_versioning = True
    environment.save()  # note: initial version created via lifecycle hook here

    original_version = EnvironmentFeatureVersion.objects.get(
        environment=environment, feature=feature
    )

    # When
    new_version = EnvironmentFeatureVersion.objects.create(
        environment=environment, feature=feature
    )

    # Then
    # the version is given a sha
    assert new_version.sha

    # and the correct feature states are cloned and added to the new version
    assert new_version.feature_states.count() == 2
    assert new_version.feature_states.filter(
        environment=environment, feature=feature, feature_segment=None, identity=None
    ).exists()
    assert new_version.feature_states.filter(
        environment=environment,
        feature=feature,
        feature_segment__segment=segment,
        identity=None,
    ).exists()

    # but the existing feature states are left untouched
    assert (
        FeatureState.objects.filter(
            environment_feature_version=original_version
        ).count()
        == 2
    )
