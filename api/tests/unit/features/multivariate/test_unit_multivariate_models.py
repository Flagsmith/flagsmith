from unittest.mock import MagicMock

from features.models import FeatureSegment, FeatureState
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)


def test_multivariate_feature_option_get_create_log_message(feature):
    # Given
    mvfo = MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")

    history_instance = MagicMock()

    # When
    msg = mvfo.get_create_log_message(history_instance)

    # Then
    assert msg == f"Multivariate option added to feature '{feature.name}'."


def test_multivariate_feature_option_get_delete_log_message_for_valid_feature(feature):
    # Given
    mvfo = MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")

    history_instance = MagicMock()

    # When
    msg = mvfo.get_delete_log_message(history_instance)

    # Then
    assert msg == f"Multivariate option removed from feature '{feature.name}'."


def test_multivariate_feature_option_get_delete_log_message_for_deleted_feature(
    feature,
):
    # Given
    mvfo = MultivariateFeatureOption.objects.create(feature=feature, string_value="foo")
    feature.delete()

    history_instance = MagicMock()

    # When
    msg = mvfo.get_delete_log_message(history_instance)

    # Then
    assert msg is None


def test_multivariate_feature_state_value_get_update_log_message_environment_default(
    multivariate_feature, environment
):
    # Given
    history_instance = MagicMock()

    mvfsv = MultivariateFeatureStateValue.objects.filter(
        feature_state__environment=environment
    ).first()

    # When
    msg = mvfsv.get_update_log_message(history_instance)

    # Then
    assert (
        msg == f"Multivariate value changed for feature '{multivariate_feature.name}'."
    )


def test_multivariate_feature_state_value_get_update_log_message_identity_override(
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


def test_multivariate_feature_state_value_get_update_log_message_segment_override(
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
