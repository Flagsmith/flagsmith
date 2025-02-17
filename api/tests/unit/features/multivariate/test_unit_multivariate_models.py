from unittest.mock import MagicMock

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE, STANDARD
from features.models import FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from segments.models import Segment


def test_multivariate_feature_option_get_create_log_message(feature):  # type: ignore[no-untyped-def]
    # Given
    mvfo = MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")

    history_instance = MagicMock()

    # When
    msg = mvfo.get_create_log_message(history_instance)

    # Then
    assert msg == f"Multivariate option added to feature '{feature.name}'."


def test_multivariate_feature_option_get_delete_log_message_for_valid_feature(feature):  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    mvfo = MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")

    history_instance = MagicMock()

    # When
    msg = mvfo.get_delete_log_message(history_instance)

    # Then
    assert msg == f"Multivariate option removed from feature '{feature.name}'."


def test_multivariate_feature_option_get_delete_log_message_for_deleted_feature(  # type: ignore[no-untyped-def]
    feature,
):
    # Given
    mvfo = MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")
    # Since the `AFTER_CREATE` hook on MultivariateFeatureOption mutates
    # mvfo.feature directly, we need to make sure that we have the latest
    # changes in order for the `AFTER_DELETE` hook to behave correctly.
    mvfo.refresh_from_db()

    feature.delete()

    history_instance = MagicMock()

    # When
    msg = mvfo.get_delete_log_message(history_instance)

    # Then
    assert msg is None


def test_multivariate_feature_state_value_get_update_log_message_environment_default(  # type: ignore[no-untyped-def]
    multivariate_feature, environment
):
    # Given
    history_instance = MagicMock()

    mvfsv = MultivariateFeatureStateValue.objects.filter(
        feature_state__environment=environment
    ).first()

    # When
    msg = mvfsv.get_update_log_message(history_instance)  # type: ignore[union-attr]

    # Then
    assert (
        msg == f"Multivariate value changed for feature '{multivariate_feature.name}'."
    )


def test_multivariate_feature_state_value_get_update_log_message_identity_override(  # type: ignore[no-untyped-def]
    multivariate_feature, environment, identity
):
    # Given
    history_instance = MagicMock()

    identity_override = FeatureState.objects.create(
        feature=multivariate_feature, identity=identity, environment=environment
    )
    mvfsv = identity_override.multivariate_feature_state_values.create(
        multivariate_feature_option=multivariate_feature.multivariate_options.first(),
        percentage_allocation=100,
    )

    # When
    msg = mvfsv.get_update_log_message(history_instance)

    # Then
    assert (
        msg
        == f"Multivariate value changed for feature '{multivariate_feature.name}' and identity '{identity.identifier}'."
    )


def test_multivariate_feature_state_value_get_update_log_message_segment_override(  # type: ignore[no-untyped-def]
    multivariate_feature, environment, segment
):
    # Given
    history_instance = MagicMock()

    feature_segment = FeatureSegment.objects.create(
        segment=segment, feature=multivariate_feature, environment=environment
    )
    segment_override = FeatureState.objects.create(
        feature=multivariate_feature,
        feature_segment=feature_segment,
        environment=environment,
    )
    mvfsv = segment_override.multivariate_feature_state_values.create(
        multivariate_feature_option=multivariate_feature.multivariate_options.first(),
        percentage_allocation=100,
    )

    # When
    msg = mvfsv.get_update_log_message(history_instance)

    # Then
    assert (
        msg
        == f"Multivariate value changed for feature '{multivariate_feature.name}' and segment '{segment.name}'."
    )


def test_deleting_last_mv_option_of_mulitvariate_feature_converts_it_into_standard(  # type: ignore[no-untyped-def]
    multivariate_feature,
):
    # Given
    assert multivariate_feature.type == MULTIVARIATE
    mv_options = multivariate_feature.multivariate_options.all()

    # First, let's delete the first mv option
    mv_options[0].delete()

    # Then - the feature should still be multivariate
    multivariate_feature.refresh_from_db()
    assert multivariate_feature.type == MULTIVARIATE

    # Next, let's delete the mv options
    for mv_option in mv_options:
        mv_option.delete()

    # Then
    multivariate_feature.refresh_from_db()
    assert multivariate_feature.type == STANDARD


def test_adding_mv_option_to_standard_feature_converts_it_into_multivariate(feature):  # type: ignore[no-untyped-def]
    # Given
    assert feature.type == STANDARD

    # When
    MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")

    # Then
    feature.refresh_from_db()
    assert feature.type == MULTIVARIATE


def test_multivariate_feature_state_value__get_skip_create_audit_log_for_identity_delete(
    multivariate_feature: MultivariateFeatureOption,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    identity_override = FeatureState.objects.create(
        feature=multivariate_feature, identity=identity, environment=environment
    )
    mvfsv = identity_override.multivariate_feature_state_values.create(
        multivariate_feature_option=multivariate_feature.multivariate_options.first(),
        percentage_allocation=100,
    )

    # When
    identity.delete()

    # Then
    mvfsv_history_instance = MultivariateFeatureStateValue.history.filter(
        id=mvfsv.id, history_type="-"
    ).first()

    assert mvfsv_history_instance.instance.get_skip_create_audit_log() is True


def test_multivariate_feature_state_value__get_skip_create_audit_log_for_segment_delete(
    multivariate_feature: MultivariateFeatureOption,
    environment: Environment,
    segment: Segment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        segment=segment, feature=multivariate_feature, environment=environment
    )
    segment_override = FeatureState.objects.create(
        feature=multivariate_feature,
        feature_segment=feature_segment,
        environment=environment,
    )
    mvfsv = segment_override.multivariate_feature_state_values.create(
        multivariate_feature_option=multivariate_feature.multivariate_options.first(),
        percentage_allocation=100,
    )

    # When
    segment.delete()

    # Then
    mvfsv_history_instance = MultivariateFeatureStateValue.history.filter(
        id=mvfsv.id, history_type="-"
    ).first()

    assert mvfsv_history_instance.instance.get_skip_create_audit_log() is True


def test_multivariate_feature_state_value__get_skip_create_audit_log_for_feature_delete(
    multivariate_feature: MultivariateFeatureOption,
    environment: Environment,
) -> None:

    # Given
    mvfsv = MultivariateFeatureStateValue.objects.filter(
        feature_state__environment=environment
    ).first()

    # When
    multivariate_feature.delete()

    # Then
    mvfsv_history_instance = MultivariateFeatureStateValue.history.filter(
        id=mvfsv.id, history_type="-"  # type: ignore[union-attr]
    ).first()

    assert mvfsv_history_instance.instance.get_skip_create_audit_log() is True
