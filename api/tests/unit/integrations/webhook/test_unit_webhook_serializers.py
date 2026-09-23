import pytest
from pytest_lazy_fixtures import lf as lazy_fixture

from environments.identities.models import Identity
from environments.models import Environment
from evaluation.services import get_identity_feature_states
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from integrations.webhook.serializers import (
    IntegrationFeatureStateSerializer,
    SegmentSerializer,
)
from segments.models import Segment


def test_integration_feature_state_serializer__multivariate_identity_override__returns_split_weight(
    environment: Environment,
    identity: Identity,
    multivariate_feature: Feature,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.order_by("id").last()
    assert option
    identity_override = FeatureState.objects.create(
        feature=multivariate_feature,
        environment=environment,
        identity=identity,
        enabled=True,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=identity_override,
        multivariate_feature_option=option,
        percentage_allocation=100,
    )
    (evaluated_feature_state,) = get_identity_feature_states(identity)

    # When
    data = IntegrationFeatureStateSerializer(evaluated_feature_state).data

    # Then
    assert data["feature_state_value"] == option.value
    assert data["percentage_allocation"] == 100.0


def test_segment_serializer__identity_matching_segment__returns_member_true(  # type: ignore[no-untyped-def]
    identity, trait, identity_matching_segment
):
    # Given
    serializer = SegmentSerializer(
        identity_matching_segment, context={"identity": identity}
    )
    # When
    data = serializer.data
    # Then
    assert data["member"] is True
    assert data["id"] == identity_matching_segment.id


@pytest.mark.parametrize(
    "segment, expected_member",
    [
        (lazy_fixture("identity_matching_segment"), True),
        (lazy_fixture("another_segment"), False),
    ],
)
def test_segment_serializer__identity_with_override__returns_segment_membership(
    identity: Identity,
    identity_featurestate: FeatureState,
    segment: Segment,
    expected_member: bool,
) -> None:
    # Given
    serializer = SegmentSerializer(segment, context={"identity": identity})

    # When
    data = serializer.data

    # Then
    assert data["member"] is expected_member
