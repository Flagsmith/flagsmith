from environments.identities.models import Identity
from features.features_service import get_overrides_data
from features.models import Feature, FeatureSegment, FeatureState


def test_feature_get_overrides_data(
    feature,
    environment,
    identity,
    segment,
    feature_segment,
    identity_featurestate,
    segment_featurestate,
):
    # Given
    # we create some other features with overrides to ensure we're only getting data
    # for each individual feature
    feature_2 = Feature.objects.create(project=feature.project, name="feature_2")
    FeatureState.objects.create(
        feature=feature_2, environment=environment, identity=identity
    )

    feature_3 = Feature.objects.create(project=feature.project, name="feature_3")
    feature_segment_for_feature_3 = FeatureSegment.objects.create(
        feature=feature_3, segment=segment, environment=environment
    )
    FeatureState.objects.create(
        feature=feature_3,
        environment=environment,
        feature_segment=feature_segment_for_feature_3,
    )

    # and an override for another identity that has been deleted
    another_identity = Identity.objects.create(
        identifier="another-identity", environment=environment
    )
    fs_to_delete = FeatureState.objects.create(
        feature=feature, environment=environment, identity=another_identity
    )
    fs_to_delete.delete()

    # When
    overrides_data = get_overrides_data(environment.id)

    # Then
    assert overrides_data[feature.id].num_identity_overrides == 1
    assert overrides_data[feature.id].num_segment_overrides == 1

    assert overrides_data[feature_2.id].num_identity_overrides == 1
    assert overrides_data[feature_2.id].num_segment_overrides == 0

    assert overrides_data[feature_3.id].num_identity_overrides is None
    assert overrides_data[feature_3.id].num_segment_overrides == 1
