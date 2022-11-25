from unittest.mock import MagicMock

import pytest
from core.request_origin import RequestOrigin
from django.db.models import Q
from flag_engine.api.document_builders import build_environment_document
from pytest_django.asserts import assertQuerysetEqual as assert_queryset_equal

from environments.models import Environment, Webhook
from features.models import Feature, FeatureState
from segments.models import Segment


@pytest.mark.parametrize(
    "allow_client_traits, request_origin, expected_result",
    (
        (True, RequestOrigin.CLIENT, True),
        (True, RequestOrigin.SERVER, True),
        (False, RequestOrigin.CLIENT, False),
        (False, RequestOrigin.SERVER, True),
    ),
)
def test_environment_trait_persistence_allowed(
    allow_client_traits, request_origin, expected_result
):
    request = MagicMock(originated_from=request_origin)
    assert (
        Environment(allow_client_traits=allow_client_traits).trait_persistence_allowed(
            request
        )
        == expected_result
    )


def test_write_environments_to_dynamodb_with_environment(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(
        Q(id=dynamo_enabled_project_environment_one.id)
    )

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )


def test_write_environments_to_dynamodb_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(Q(project=dynamo_enabled_project))

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0], Environment.objects.filter(project=dynamo_enabled_project)
    )


def test_write_environments_to_dynamodb_with_environment_and_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(
        Q(id=dynamo_enabled_project_environment_one.id)
    )

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )


@pytest.mark.parametrize(
    "value, identity_id, identifier",
    (
        (True, None, None),
        (False, None, None),
        ("foo", None, None),
        (1, None, None),
        ("foo", 1, "identity-identifier"),
    ),
)
def test_webhook_generate_webhook_feature_state_data(
    feature, environment, value, identity_id, identifier
):
    # Given
    enabled = True

    # When
    data = Webhook.generate_webhook_feature_state_data(
        feature, environment, enabled, value, identity_id, identifier
    )

    # Then
    assert data


@pytest.mark.parametrize("identity_id, identifier", ((1, None), (None, "identifier")))
def test_webhook_generate_webhook_feature_state_data_identity_error_conditions(
    mocker, identity_id, identifier
):
    # Given
    enabled = True
    value = "foo"
    feature = mocker.MagicMock(id="feature")
    environment = mocker.MagicMock(id="environment")

    # When
    with pytest.raises(ValueError):
        Webhook.generate_webhook_feature_state_data(
            feature,
            environment,
            enabled,
            value,
            identity_id,
            identifier,
        )

    # Then
    # exception raised


def test_webhook_generate_webhook_feature_state_data_raises_error_segment_and_identity(
    mocker,
):
    # Given
    enabled = True
    value = "foo"
    feature = mocker.MagicMock(id="feature")
    environment = mocker.MagicMock(id="environment")
    feature_segment = mocker.MagicMock(id="feature_segment")
    identity_id = 1
    identifier = "identity"

    # When
    with pytest.raises(ValueError):
        Webhook.generate_webhook_feature_state_data(
            feature=feature,
            environment=environment,
            enabled=enabled,
            value=value,
            identity_id=identity_id,
            identity_identifier=identifier,
            feature_segment=feature_segment,
        )

    # Then
    # exception raised


def test_environment_get_environment_document(environment, django_assert_num_queries):
    # Given

    # When
    with django_assert_num_queries(4):
        environment_document = Environment.get_environment_document(environment.api_key)

    # Then
    assert environment_document
    assert environment_document["api_key"] == environment.api_key


def test_environment_get_environment_document_with_caching_when_document_in_cache(
    environment, django_assert_num_queries, settings, mocker
):
    # Given
    settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS = 60

    mocked_environment_document_cache = mocker.patch(
        "environments.models.environment_document_cache"
    )
    mocked_environment_document_cache.get.return_value = build_environment_document(
        environment
    )

    # When
    with django_assert_num_queries(0):
        environment_document = Environment.get_environment_document(environment.api_key)

    # Then
    assert environment_document
    assert environment_document["api_key"] == environment.api_key


def test_environment_get_environment_document_with_caching_when_document_not_in_cache(
    environment, django_assert_num_queries, settings, mocker
):
    # Given
    settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS = 60

    mocked_environment_document_cache = mocker.patch(
        "environments.models.environment_document_cache"
    )
    mocked_environment_document_cache.get.return_value = None

    # When
    with django_assert_num_queries(4):
        environment_document = Environment.get_environment_document(environment.api_key)

    # Then
    assert environment_document
    assert environment_document["api_key"] == environment.api_key

    mocked_environment_document_cache.set.assert_called_once_with(
        environment.api_key, environment_document
    )


def test_creating_a_feature_with_defaults_does_not_set_defaults_if_disabled(project):
    # Given
    project.prevent_flag_defaults = True
    project.save()

    default_enabled = True
    initial_value = "default"
    feature = Feature.objects.create(
        project=project,
        name="test_feature",
        default_enabled=default_enabled,
        initial_value=initial_value,
    )

    environment = Environment(project=project, name="test environment")

    # When
    environment.save()

    # Then
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    assert feature_state.enabled is False
    assert feature_state.get_feature_state_value() is None


def test_get_segments_returns_no_segments_if_no_overrides(environment, segment):
    assert environment.get_segments_from_cache() == []


def test_get_segments_returns_only_segments_that_have_an_override(
    environment, segment, segment_featurestate, mocker, monkeypatch
):
    # Given
    mock_environment_segments_cache = mocker.MagicMock()
    mock_environment_segments_cache.get.return_value = None

    monkeypatch.setattr(
        "environments.models.environment_segments_cache",
        mock_environment_segments_cache,
    )

    Segment.objects.create(project=environment.project, name="another segment")

    # When
    segments = environment.get_segments_from_cache()

    # Then
    assert segments == [segment]

    mock_environment_segments_cache.set.assert_called_once_with(
        environment.id, segments
    )


def test_get_segments_from_cache_does_not_hit_db_if_cache_hit(
    environment,
    segment,
    segment_featurestate,
    mocker,
    monkeypatch,
    django_assert_num_queries,
):
    # Given
    mock_environment_segments_cache = mocker.MagicMock()
    mock_environment_segments_cache.get.return_value = [segment]

    monkeypatch.setattr(
        "environments.models.environment_segments_cache",
        mock_environment_segments_cache,
    )

    # When
    with django_assert_num_queries(0):
        segments = environment.get_segments_from_cache()

    # Then
    assert segments == [segment_featurestate.feature_segment.segment]

    mock_environment_segments_cache.set.assert_not_called()
