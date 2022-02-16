from django.utils import timezone

from environments.identities.models import Identity
from features.models import Feature, FeatureState


def test_identity_get_all_feature_states_gets_latest_committed_version(environment):
    # Given
    identity = Identity.objects.create(identifier="identity", environment=environment)

    feature = Feature.objects.create(
        name="versioned_feature",
        project=environment.project,
        default_enabled=False,
        initial_value="v1",
    )

    now = timezone.now()

    # creating the feature above will have created a feature state with version=1,
    # now we create 2 more versions...
    # one of which is live...
    feature_state_v2 = FeatureState.objects.create(
        feature=feature,
        version=2,
        live_from=now,
        enabled=True,
        environment=environment,
    )
    feature_state_v2.feature_state_value.string_value = "v2"
    feature_state_v2.feature_state_value.save()

    # and one which isn't
    feature_state_v3 = FeatureState.objects.create(
        feature=feature,
        version=3,
        live_from=None,
        enabled=False,
        environment=environment,
    )
    feature_state_v3.feature_state_value.string_value = "v3"
    feature_state_v3.feature_state_value.save()

    # When
    identity_feature_states = identity.get_all_feature_states()

    # Then
    identity_feature_state = next(
        filter(lambda fs: fs.feature == feature, identity_feature_states)
    )
    assert identity_feature_state.get_feature_state_value() == "v2"
