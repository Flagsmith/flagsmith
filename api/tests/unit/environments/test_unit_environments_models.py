import random
import typing
from copy import copy
from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock, Mock

import pytest
from common.test_tools import AssertMetricFixture
from django.db.models import Count, Q
from django.test import override_settings
from django.utils import timezone
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django import DjangoAssertNumQueries
from pytest_django.asserts import assertQuerySetEqual as assert_queryset_equal
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.constants import STRING
from core.request_origin import RequestOrigin
from environments.identities.models import Identity
from environments.metrics import CACHE_HIT, CACHE_MISS
from environments.models import (
    Environment,
    EnvironmentAPIKey,
    Webhook,
    environment_cache,
)
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import enable_v2_versioning
from features.versioning.versioning_service import (
    get_environment_flags_queryset,
)
from features.workflows.core.models import ChangeRequest
from organisations.models import Organisation, OrganisationRole
from projects.models import EdgeV2MigrationStatus, Project
from segments.models import Segment
from tests.types import EnableFeaturesFixture
from users.models import FFAdminUser
from util.mappers import map_environment_to_environment_document

if typing.TYPE_CHECKING:
    from django.db.models import Model


def test_environment_create__with_existing_feature__creates_feature_states(
    organisation: Organisation,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    assert not feature.feature_states.exists()

    # When
    Environment.objects.create(name="New Environment", project=project)

    # Then
    # A new environment comes with a new feature state.
    assert feature.feature_states.count() == 1


def test_environment_save__feature_default_enabled_changed__preserves_feature_state_count(
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature.default_enabled = True
    feature.save()

    # When
    environment.save()

    # Then
    assert FeatureState.objects.count() == 1


def test_environment_clone__default__does_not_modify_original_instance(
    environment: Environment,
) -> None:
    # Given
    original_name = environment.name
    original_api_key = environment.api_key

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert clone.name != original_name
    assert clone.api_key != original_api_key


def test_environment_clone__with_feature__creates_feature_states(  # type: ignore[no-untyped-def]
    environment: Environment, feature: Feature
):
    # Given
    assert feature.feature_states.count() == 1

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert feature.feature_states.count() == 2
    feature_states = FeatureState.objects.filter(environment=clone)
    assert feature_states.count() == 1


def test_environment_clone__with_feature__does_not_modify_source_feature_state(  # type: ignore[no-untyped-def]
    environment: Environment,
    feature: Feature,
):
    # Given
    source_feature_state_before_clone = feature.feature_states.first()

    # When
    environment.clone(name="Cloned env")
    source_feature_state_after_clone = FeatureState.objects.filter(
        environment=environment
    ).first()

    # Then
    assert source_feature_state_before_clone == source_feature_state_after_clone


def test_environment_clone__with_identities__does_not_clone_identities(  # type: ignore[no-untyped-def]
    environment: Environment,
):
    # Given
    Identity.objects.create(environment=environment, identifier="test_identity")

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert clone.identities.count() == 0


def test_environment_clone__feature_enabled__clones_enabled_state(
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature_state = feature.feature_states.first()
    assert feature_state.enabled is False  # type: ignore[union-attr]

    # Enable the feature in the source environment
    feature_state.enabled = True  # type: ignore[union-attr]
    feature_state.save()  # type: ignore[union-attr]

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert clone.feature_states.first().enabled is True

    clone.refresh_from_db()
    assert clone.is_creating is False


def test_environment_clone__multivariate_feature__clones_mv_state_values(
    environment: Environment,
    project: Project,
) -> None:
    # Given
    mv_feature = Feature.objects.create(
        type=MULTIVARIATE,
        name="mv_feature",
        initial_value="foo",
        project=project,
    )
    variant_1 = MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type=STRING,
        string_value="bar",
    )

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    cloned_mv_feature_state = clone.feature_states.get(feature=mv_feature)
    assert cloned_mv_feature_state.multivariate_feature_state_values.count() == 1

    original_mv_fs_value = FeatureState.objects.get(
        environment=environment, feature=mv_feature
    ).multivariate_feature_state_values.first()
    cloned_mv_fs_value = (
        cloned_mv_feature_state.multivariate_feature_state_values.first()
    )

    assert original_mv_fs_value != cloned_mv_fs_value
    assert (
        original_mv_fs_value.multivariate_feature_option
        == cloned_mv_fs_value.multivariate_feature_option
        == variant_1
    )
    assert (
        original_mv_fs_value.percentage_allocation
        == cloned_mv_fs_value.percentage_allocation
        == 10
    )


@mock.patch("environments.models.environment_cache")
def test_get_from_cache__cache_miss__stores_environment_in_cache(
    mock_cache: MagicMock,
    environment: Environment,
) -> None:
    # Given
    mock_cache.get.return_value = None

    # When
    cached_environment = Environment.get_from_cache(environment.api_key)

    # Then
    assert cached_environment == environment
    mock_cache.set.assert_called_with(environment.api_key, environment, timeout=60)


def test_get_from_cache__no_matching_environment__returns_none(
    environment: Environment,
) -> None:
    # Given
    api_key = "no-matching-env"

    # When
    env = Environment.get_from_cache(api_key)

    # Then
    assert env is None


def test_get_from_cache__environment_api_key_model_key__returns_environment(
    environment: Environment,
) -> None:
    # Given
    api_key = EnvironmentAPIKey.objects.create(name="Some key", environment=environment)

    # When
    environment_from_cache = Environment.get_from_cache(api_key=api_key.key)

    # Then
    assert environment_from_cache == environment


def test_get_from_cache__null_api_key__returns_none(
    environment: Environment,
) -> None:
    # Given / When
    environment2 = Environment.get_from_cache(None)

    # Then
    assert environment2 is None


@override_settings(
    CACHE_BAD_ENVIRONMENTS_SECONDS=60, CACHE_BAD_ENVIRONMENTS_AFTER_FAILURES=1
)
def test_get_from_cache__bad_api_key_cached__does_not_hit_database(
    django_assert_num_queries: DjangoAssertNumQueries,
    db: None,
) -> None:
    # Given
    api_key = "bad-key"

    # When / Then
    with django_assert_num_queries(1):
        [Environment.get_from_cache(api_key) for _ in range(10)]


def test_environment_api_key_is_valid__non_expired_active_key__returns_true(  # type: ignore[no-untyped-def]
    environment,
):
    # Given / When
    result = EnvironmentAPIKey.objects.create(
        environment=environment,
        key="ser.random_key",
        name="test_key",
    ).is_valid

    # Then
    assert result is True


def test_environment_api_key_is_valid__active_key_with_future_expiry__returns_true(  # type: ignore[no-untyped-def]
    environment,
):
    # Given / When
    result = EnvironmentAPIKey.objects.create(
        environment=environment,
        key="ser.random_key",
        name="test_key",
        expires_at=timezone.now() + timedelta(days=5),
    ).is_valid

    # Then
    assert result is True


def test_environment_api_key_is_valid__expired_active_key__returns_false(  # type: ignore[no-untyped-def]
    environment,
):
    # Given / When
    result = EnvironmentAPIKey.objects.create(
        environment=environment,
        key="ser.random_key",
        name="test_key",
        expires_at=timezone.now() - timedelta(seconds=1),
    ).is_valid

    # Then
    assert result is False


def test_environment_api_key_is_valid__non_expired_inactive_key__returns_false(  # type: ignore[no-untyped-def]
    environment,
):
    # Given / When
    result = EnvironmentAPIKey.objects.create(
        environment=environment, key="ser.random_key", name="test_key", active=False
    ).is_valid

    # Then
    assert result is False


def test_get_from_cache__multiple_api_keys_exist__returns_environment_for_each(  # type: ignore[no-untyped-def]
    environment,
):
    # Given
    environment_api_keys = [
        EnvironmentAPIKey.objects.create(environment=environment, name=f"test_key_{i}")
        for i in range(2)
    ]

    # When
    retrieved_environments = [
        Environment.get_from_cache(environment.api_key),
        *[
            Environment.get_from_cache(environment_api_key.key)
            for environment_api_key in environment_api_keys
        ],
    ]

    # Then
    assert all(
        retrieved_environment == environment
        for retrieved_environment in retrieved_environments
    )


def test_get_from_cache__environment_api_key__sets_cache_correctly(  # type: ignore[no-untyped-def]
    environment, environment_api_key, mocker
):
    # Given / When
    returned_environment = Environment.get_from_cache(environment_api_key.key)

    # Then
    assert returned_environment == environment
    assert environment == environment_cache.get(environment_api_key.key)


def test_environment_updated_at__environment_audit_log_created__updates_timestamp(
    environment,
):  # type: ignore[no-untyped-def]
    # Given / When
    audit_log = AuditLog.objects.create(
        environment=environment, project=environment.project, log="random_audit_log"
    )

    # Then
    environment.refresh_from_db()
    assert environment.updated_at == audit_log.created_date


def test_environment_updated_at__project_audit_log_created__updates_timestamp(
    environment,
):  # type: ignore[no-untyped-def]
    # Given / When
    audit_log = AuditLog.objects.create(
        project=environment.project, log="random_audit_log"
    )

    # Then
    environment.refresh_from_db()
    assert environment.updated_at == audit_log.created_date


def test_environment_updated_at__change_request_audit_log_created__does_not_update(
    environment,
):  # type: ignore[no-untyped-def]
    # Given
    updated_at_before_audit_log = environment.updated_at

    # When
    audit_log = AuditLog.objects.create(
        environment=environment,
        log="random_test",
        related_object_type=RelatedObjectType.CHANGE_REQUEST.name,
    )

    # Then
    assert environment.updated_at == updated_at_before_audit_log
    assert environment.updated_at != audit_log.created_date


def test_environment_save__api_key_changed__clears_cache_with_original_key(
    mocker, project
):  # type: ignore[no-untyped-def]
    # Given
    mock_environment_cache = mocker.patch("environments.models.environment_cache")
    environment = Environment.objects.create(name="test environment", project=project)

    # perform an update of the name to verify basic functionality
    environment.name = "updated"
    environment.save()

    # and update the api key to verify that the original api key is used to clear cache
    old_key = copy(environment.api_key)
    new_key = "some-new-key"
    environment.api_key = new_key

    # When
    environment.save()

    # Then
    mock_calls = mock_environment_cache.delete_many.mock_calls
    assert len(mock_calls) == 2
    assert mock_calls[0][1][0] == mock_calls[1][1][0] == [old_key]


@pytest.mark.parametrize(
    "allow_client_traits, request_origin, expected_result",
    (
        (True, RequestOrigin.CLIENT, True),
        (True, RequestOrigin.SERVER, True),
        (False, RequestOrigin.CLIENT, False),
        (False, RequestOrigin.SERVER, True),
    ),
)
def test_trait_persistence_allowed__parametrised_origins__returns_expected(  # type: ignore[no-untyped-def]
    allow_client_traits, request_origin, expected_result
):
    # Given
    request = MagicMock(originated_from=request_origin)

    # When
    result = Environment(
        allow_client_traits=allow_client_traits
    ).trait_persistence_allowed(request)

    # Then
    assert result == expected_result


def test_write_environment_documents__single_environment__writes_correct_queryset(  # type: ignore[no-untyped-def]
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environment_documents(
        environment_id=dynamo_enabled_project_environment_one.id
    )

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )


def test_write_environment_documents__project_id__writes_all_project_environments(  # type: ignore[no-untyped-def]
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environment_documents(project_id=dynamo_enabled_project.id)

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0], Environment.objects.filter(project=dynamo_enabled_project)
    )


def test_write_environment_documents__environment_id_provided__writes_single_environment(  # type: ignore[no-untyped-def]
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environment_documents(
        environment_id=dynamo_enabled_project_environment_one.id
    )

    # Then
    args, kwargs = mock_dynamo_env_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0],
        Environment.objects.filter(id=dynamo_enabled_project_environment_one.id),
    )


def test_write_environments_to_dynamodb__project_environments_v2_migrated__call_expected(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamo_enabled_project_environment_two: Environment,
    mock_dynamo_env_wrapper: Mock,
    mock_dynamo_env_v2_wrapper: Mock,
) -> None:
    # Given
    dynamo_enabled_project.edge_v2_migration_status = EdgeV2MigrationStatus.COMPLETE
    dynamo_enabled_project.save()
    mock_dynamo_env_v2_wrapper.is_enabled = True

    # When
    Environment.write_environment_documents(project_id=dynamo_enabled_project.id)

    # Then
    args, kwargs = mock_dynamo_env_v2_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0], Environment.objects.filter(project=dynamo_enabled_project)
    )


def test_write_environment_documents__v2_migrated_wrapper_disabled__wrapper_not_called(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamo_enabled_project_environment_two: Environment,
    mock_dynamo_env_wrapper: Mock,
    mock_dynamo_env_v2_wrapper: Mock,
) -> None:
    # Given
    mock_dynamo_env_v2_wrapper.is_enabled = False
    dynamo_enabled_project.edge_v2_migration_status = EdgeV2MigrationStatus.COMPLETE
    dynamo_enabled_project.save()

    # When
    Environment.write_environment_documents(project_id=dynamo_enabled_project.id)

    # Then
    mock_dynamo_env_v2_wrapper.write_environments.assert_not_called()


@pytest.mark.parametrize(
    "edge_v2_migration_status",
    (
        EdgeV2MigrationStatus.NOT_STARTED,
        EdgeV2MigrationStatus.IN_PROGRESS,
    ),
)
def test_write_environments_to_dynamodb__project_environments_v2_not_migrated__wrapper_not_called(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamo_enabled_project_environment_two: Environment,
    mock_dynamo_env_wrapper: Mock,
    mock_dynamo_env_v2_wrapper: Mock,
    edge_v2_migration_status: str,
) -> None:
    # Given
    dynamo_enabled_project.edge_v2_migration_status = edge_v2_migration_status
    dynamo_enabled_project.save()
    mock_dynamo_env_v2_wrapper.is_enabled = True

    # When
    Environment.write_environment_documents(project_id=dynamo_enabled_project.id)

    # Then
    mock_dynamo_env_v2_wrapper.write_environments.assert_not_called()


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
def test_generate_webhook_feature_state_data__valid_params__returns_data(  # type: ignore[no-untyped-def]
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
def test_generate_webhook_feature_state_data__incomplete_identity_params__raises_value_error(  # type: ignore[no-untyped-def]
    mocker, identity_id, identifier
):
    # Given
    enabled = True
    value = "foo"
    feature = mocker.MagicMock(id="feature")
    environment = mocker.MagicMock(id="environment")

    # When / Then
    with pytest.raises(ValueError):
        Webhook.generate_webhook_feature_state_data(
            feature,
            environment,
            enabled,
            value,
            identity_id,
            identifier,
        )


def test_generate_webhook_feature_state_data__segment_and_identity__raises_value_error(  # type: ignore[no-untyped-def]
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

    # When / Then
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


def test_get_environment_document__valid_api_key__returns_document(
    environment, django_assert_num_queries
):  # type: ignore[no-untyped-def]
    # Given

    # When
    with django_assert_num_queries(3):
        environment_document = Environment.get_environment_document(environment.api_key)

    # Then
    assert environment_document
    assert environment_document["api_key"] == environment.api_key


def test_get_environment_document__document_in_cache__returns_cached_document(  # type: ignore[no-untyped-def]
    environment, django_assert_num_queries, settings, mocker
):
    # Given
    settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS = 60

    mocked_environment_document_cache = mocker.patch(
        "environments.models.environment_document_cache"
    )
    mocked_environment_document_cache.get.return_value = (
        map_environment_to_environment_document(environment)
    )

    # When
    with django_assert_num_queries(0):
        environment_document = Environment.get_environment_document(environment.api_key)

    # Then
    assert environment_document
    assert environment_document["api_key"] == environment.api_key


def test_get_environment_document__document_not_in_cache__fetches_and_caches(  # type: ignore[no-untyped-def]
    environment, django_assert_num_queries, settings, mocker
):
    # Given
    settings.CACHE_ENVIRONMENT_DOCUMENT_SECONDS = 60

    mocked_environment_document_cache = mocker.patch(
        "environments.models.environment_document_cache"
    )
    mocked_environment_document_cache.get.return_value = None

    # When
    with django_assert_num_queries(3):
        environment_document = Environment.get_environment_document(environment.api_key)

    # Then
    assert environment_document
    assert environment_document["api_key"] == environment.api_key

    mocked_environment_document_cache.set.assert_called_once_with(
        environment.api_key, environment_document
    )


def test_environment_save__prevent_flag_defaults_enabled__ignores_feature_defaults(
    project,
):  # type: ignore[no-untyped-def]
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
    assert not feature_state.get_feature_state_value()


def test_get_segments_from_cache__no_overrides__returns_empty_list(
    environment, segment
):  # type: ignore[no-untyped-def]
    # Given / When
    result = environment.get_segments_from_cache()

    # Then
    assert result == []


def test_get_segments_from_cache__segment_override_exists__returns_overridden_segment(  # type: ignore[no-untyped-def]
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


def test_get_segments_from_cache__cache_hit__does_not_query_database(  # type: ignore[no-untyped-def]
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


@pytest.mark.parametrize(
    "environment_value, project_value, expected_result",
    (
        (True, True, True),
        (True, False, True),
        (False, True, False),
        (False, False, False),
        (None, True, True),
        (None, False, False),
    ),
)
def test_get_hide_disabled_flags__parametrised_values__returns_expected(  # type: ignore[no-untyped-def]
    project, environment, environment_value, project_value, expected_result
):
    # Given
    project.hide_disabled_flags = project_value
    project.save()

    environment.hide_disabled_flags = environment_value
    environment.save()

    # When
    result = environment.get_hide_disabled_flags()

    # Then
    assert result is expected_result


def test_environment_api_key_save__dynamo_enabled__creates_dynamo_document(  # type: ignore[no-untyped-def]
    dynamo_enabled_project_environment_one: Environment,
    mocker: MockerFixture,
    flagsmith_environment_api_key_table: "Table",
):
    # Given
    mocker.patch(
        "environments.models.DynamoEnvironmentAPIKeyWrapper.table",
        new_callable=mocker.PropertyMock,
        return_value=flagsmith_environment_api_key_table,
    )
    # When
    api_key = EnvironmentAPIKey.objects.create(
        name="Some key", environment=dynamo_enabled_project_environment_one
    )

    # Then
    response = flagsmith_environment_api_key_table.get_item(Key={"key": api_key.key})
    assert response["Item"]["key"] == api_key.key


def test_environment_api_key_delete__dynamo_enabled__deletes_dynamo_document(  # type: ignore[no-untyped-def]
    dynamo_enabled_project_environment_one: Environment,
    mocker: MockerFixture,
    flagsmith_environment_api_key_table: "Table",
):
    # Given
    mocker.patch(
        "environments.models.DynamoEnvironmentAPIKeyWrapper.table",
        new_callable=mocker.PropertyMock,
        return_value=flagsmith_environment_api_key_table,
    )
    api_key = EnvironmentAPIKey.objects.create(
        name="Some key", environment=dynamo_enabled_project_environment_one
    )
    assert flagsmith_environment_api_key_table.scan()["Count"] == 1

    # When
    api_key.delete()

    # Then
    assert flagsmith_environment_api_key_table.scan()["Count"] == 0


def test_environment_delete__dynamo_enabled__creates_delete_dynamo_task(
    dynamo_enabled_project_environment_one: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    mocked_task = mocker.patch("environments.tasks.delete_environment_from_dynamo")
    mocker.patch(
        "environments.models.DynamoEnvironmentWrapper.is_enabled",
        new_callable=mocker.PropertyMock,
        return_value=True,
    )

    # When
    dynamo_enabled_project_environment_one.delete()

    # Then
    mocked_task.delay.assert_called_once_with(
        args=(
            dynamo_enabled_project_environment_one.api_key,
            dynamo_enabled_project_environment_one.id,
        )
    )


def test_environment_api_key_delete__non_edge_project__does_not_call_dynamo_delete(
    environment_api_key: EnvironmentAPIKey, mocker: MockerFixture
) -> None:
    # Given
    mocked_environment_api_key_wrapper = mocker.patch(
        "environments.models.environment_api_key_wrapper", autospec=True
    )
    # When
    environment_api_key.delete()

    # Then
    mocked_environment_api_key_wrapper.delete_api_key.assert_not_called()


def test_environment_api_key_save__non_edge_project__does_not_call_dynamo_write(  # type: ignore[no-untyped-def]
    environment, mocker
):
    # Given
    mocked_environment_api_key_wrapper = mocker.patch(
        "environments.models.environment_api_key_wrapper", autospec=True
    )
    # When
    EnvironmentAPIKey.objects.create(name="Some key", environment=environment)

    # Then
    mocked_environment_api_key_wrapper.write_api_key.assert_not_called()


def test_environment_delete__committed_change_request__soft_deletes(
    organisation: "Organisation",
    environment: Environment,
    change_request: "ChangeRequest",
    change_request_feature_state: FeatureState,
    django_user_model: typing.Type["Model"],
) -> None:
    # Given
    user = django_user_model.objects.create(email="test@example.com")  # type: ignore[attr-defined]
    user.add_organisation(organisation, OrganisationRole.ADMIN)
    change_request.approve(user)
    change_request.commit(user)

    # When
    environment.delete()

    # Then
    assert environment.deleted_at is not None


def test_environment_create__v2_versioning_with_features__creates_feature_versions(
    project: "Project",
) -> None:
    # Given
    Feature.objects.create(name="test_feature_1", project=project)
    Feature.objects.create(name="test_feature_2", project=project)

    # When
    environment = Environment.objects.create(
        project=project, name="Environment 1", use_v2_feature_versioning=True
    )

    # Then
    assert (
        EnvironmentFeatureVersion.objects.filter(environment=environment).count() == 2
    )
    assert environment.feature_states.count() == 2


def test_environment_clone__v2_versioning_with_segments__clones_latest_feature_states(
    feature: Feature,
    feature_state: FeatureState,
    segment: Segment,
    segment_featurestate: FeatureState,
    environment: Environment,
) -> None:
    # Given
    expected_environment_fs_enabled_value = True
    expected_segment_fs_enabled_value = True

    # First let's create some new versions via the old versioning methods
    feature_state.clone(environment, version=2)
    feature_state.clone(environment, version=3)

    # and a draft version
    feature_state.clone(environment, as_draft=True)

    # Now let's enable v2 versioning for the environment
    enable_v2_versioning(environment.id)
    environment.refresh_from_db()

    # Finally, let's create another version using the new versioning methods
    # and update some values on the feature states in it.
    v2 = EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment
    )
    v2.feature_states.filter(feature_segment__isnull=True).update(
        enabled=expected_environment_fs_enabled_value
    )
    v2.feature_states.filter(feature_segment__isnull=False).update(
        enabled=expected_segment_fs_enabled_value
    )
    v2.publish()

    # When
    cloned_environment = environment.clone(name="Cloned environment")

    # Then
    assert cloned_environment.use_v2_feature_versioning is True

    cloned_environment_flags = get_environment_flags_queryset(cloned_environment)

    assert (
        cloned_environment_flags.get(feature_segment__isnull=True).enabled
        is expected_environment_fs_enabled_value
    )
    assert (
        cloned_environment_flags.get(feature_segment__segment=segment).enabled
        is expected_segment_fs_enabled_value
    )


def test_environment_clone__async_mode__schedules_clone_task(
    environment: Environment, mocker: MockerFixture
) -> None:
    # Given
    mocked_clone_environment_fs_task = mocker.patch(
        "environments.tasks.clone_environment_feature_states"
    )

    # When
    cloned_environment = environment.clone(
        name="Cloned environment", clone_feature_states_async=True
    )

    # Then
    assert cloned_environment.id != environment.id
    assert cloned_environment.is_creating is True
    mocked_clone_environment_fs_task.delay.assert_called_once_with(
        kwargs={
            "source_environment_id": environment.id,
            "clone_environment_id": cloned_environment.id,
        }
    )


def test_environment_delete__default__removes_environment_document_cache(
    environment: Environment,
    persistent_environment_document_cache: MagicMock,
) -> None:
    # Given / When
    environment.delete()

    # Then
    persistent_environment_document_cache.delete.assert_called_once_with(
        environment.api_key
    )


def test_environment_save__api_key_changed__updates_environment_document_cache(
    environment: Environment,
    persistent_environment_document_cache: MagicMock,
) -> None:
    # Given
    old_api_key = copy(environment.api_key)
    new_api_key = "new-key"

    # When
    environment.api_key = new_api_key
    environment.save()

    # Then
    persistent_environment_document_cache.delete.assert_called_once_with(old_api_key)
    persistent_environment_document_cache.set_many.assert_called_once_with(
        {new_api_key: map_environment_to_environment_document(environment)}
    )


def test_get_environment_document__cache_hit__triggers_cache_hit_metric(
    environment: Environment,
    persistent_environment_document_cache: MagicMock,
    populate_environment_document_cache: None,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given / When
    Environment.get_environment_document(environment.api_key)

    # Then
    assert_metric(
        name="flagsmith_environment_document_cache_queries_total",
        labels={
            "result": CACHE_HIT,
        },
        value=1.0,
    )


def test_get_environment_document__cache_miss__triggers_cache_miss_metric(
    environment: Environment,
    persistent_environment_document_cache: MagicMock,
    assert_metric: AssertMetricFixture,
) -> None:
    # Given & When
    Environment.get_environment_document(environment.api_key)

    # Then
    assert_metric(
        name="flagsmith_environment_document_cache_queries_total",
        labels={
            "result": CACHE_MISS,
        },
        value=1.0,
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "total_features, feature_enabled_count, segment_overrides_count, change_request_count, scheduled_change_count",
    [
        (0, 0, 0, 0, 0),
        (10, 4, 9, 4, 3),
        (10, 10, 10, 10, 10),
        (5, 10, 6, 3, 2),
        (21, 14, 8, 13, 2),
    ],
)
def test_environment_metric_queries__parametrised_counts__return_expected_values(
    project: Project,
    admin_user: FFAdminUser,
    total_features: int,
    feature_enabled_count: int,
    segment_overrides_count: int,
    change_request_count: int,
    scheduled_change_count: int,
) -> None:
    # Given
    env = Environment.objects.create(name="env", project=project)
    env.minimum_change_request_approvals = 1
    env.save()

    features = []
    version = 0
    for i in range(total_features):
        f = Feature.objects.create(project=project, name=f"f-{i}")
        FeatureState.objects.update_or_create(
            feature=f, environment=env, identity=None, enabled=False, version=version
        )
        features.append(f)
        version += 1

    for i in range(min(feature_enabled_count, total_features)):
        # Create old feature_state versions that should not be counted
        FeatureState.objects.create(
            feature=features[i],
            environment=env,
            identity=None,
            enabled=True,
            version=version,
        )
        version += 1

        FeatureState.objects.update_or_create(
            feature=features[i],
            environment=env,
            identity=None,
            enabled=True,
            version=version,
        )
        version += 1

    for i in range(segment_overrides_count):
        segment = Segment.objects.create(project=project, name=f"s-{i}")
        f = random.choice(features)
        fs = FeatureSegment.objects.create(feature=f, segment=segment, environment=env)
        FeatureState.objects.update_or_create(
            feature=f,
            environment=env,
            feature_segment=fs,
            identity=None,
            enabled=False,
            version=version,
        )
        version += 1

    for i in range(change_request_count):
        ChangeRequest.objects.create(
            environment=env, title=f"CR-{i}", user_id=admin_user.id
        )
        version += 1

    for i in range(scheduled_change_count):
        cr = ChangeRequest.objects.create(
            environment=env,
            title=f"Scheduled-CR-{i}",
            user_id=admin_user.id,
            committed_at=timezone.now(),
        )
        FeatureState.objects.update_or_create(
            feature=random.choice(features),
            environment=env,
            change_request=cr,
            identity=None,
            enabled=True,
            live_from=timezone.now() + timedelta(days=5),
            version=version,
        )
        version += 1

    # When
    features_agg = env.get_features_metrics_queryset().aggregate(
        total=Count("id"),
        enabled=Count("id", filter=Q(enabled=True)),
    )
    segment_count = env.get_segment_metrics_queryset().count()
    identity_override_count = env.get_identity_overrides_queryset().count()
    change_request_count_result = env.get_change_requests_metrics_queryset().count()
    scheduled_count_result = env.get_scheduled_metrics_queryset().count()

    # Then
    assert features_agg["total"] == total_features
    assert features_agg["enabled"] == min(feature_enabled_count, total_features)
    assert segment_count == segment_overrides_count
    assert change_request_count_result == change_request_count
    assert scheduled_count_result == scheduled_change_count
    assert identity_override_count == 0


def test_environment_create__v2_versioning_flag_enabled__enables_v2_versioning(
    project: Project,
    feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("enable_feature_versioning_for_new_environments")

    # When
    new_environment = Environment.objects.create(
        name="new-environment",
        project=project,
    )

    # Then
    assert EnvironmentFeatureVersion.objects.filter(
        environment=new_environment, feature=feature
    ).exists()
    assert new_environment.use_v2_feature_versioning


def test_environment_clone__from_v2_versioned_environment__preserves_v2_versioning(
    project: Project,
    environment_v2_versioning: Environment,
    feature: Feature,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("enable_feature_versioning_for_new_environments")

    # When
    new_environment = environment_v2_versioning.clone(name="new-environment")

    # Then
    assert EnvironmentFeatureVersion.objects.filter(
        environment=new_environment, feature=feature
    ).exists()
    assert new_environment.use_v2_feature_versioning


def test_environment_clone__from_v1_with_v2_flag_enabled__upgrades_to_v2_versioning(
    project: Project,
    environment: Environment,
    feature: Feature,
    segment_featurestate: FeatureState,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("enable_feature_versioning_for_new_environments")

    # Ensure that v2 versioning is not enabled for this test as we explicitly
    # want to test that we can clone from v1 -> v2 successsfully.
    environment.use_v2_feature_versioning = False
    environment.save()

    # When
    new_environment = environment.clone(name="new-environment")

    # Then
    assert new_environment.use_v2_feature_versioning

    # we only expect a single environment feature version as we are essentially
    # taking a snapshot and creating a new environment.
    efv = EnvironmentFeatureVersion.objects.get(
        environment=new_environment, feature=feature
    )

    # But we expect 2 feature states, each with the same version
    latest_feature_states = get_environment_flags_queryset(new_environment)
    assert latest_feature_states.count() == 2
    assert {fs.environment_feature_version for fs in latest_feature_states} == {efv}
