import typing
from copy import copy
from datetime import timedelta
from unittest import mock
from unittest.mock import MagicMock, Mock

import pytest
from core.constants import STRING
from core.request_origin import RequestOrigin
from django.test import override_settings
from django.utils import timezone
from mypy_boto3_dynamodb.service_resource import Table
from pytest_django import DjangoAssertNumQueries
from pytest_django.asserts import assertQuerysetEqual as assert_queryset_equal
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.identities.models import Identity
from environments.models import (
    Environment,
    EnvironmentAPIKey,
    Webhook,
    environment_cache,
)
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.versioning.models import EnvironmentFeatureVersion
from organisations.models import Organisation, OrganisationRole
from projects.models import IdentityOverridesV2MigrationStatus, Project
from segments.models import Segment
from util.mappers import map_environment_to_environment_document

if typing.TYPE_CHECKING:
    from django.db.models import Model

    from features.workflows.core.models import ChangeRequest


def test_on_environment_create_makes_feature_states(
    organisation: Organisation,
    feature: Feature,
    project: Project,
) -> None:
    # Given
    assert feature.feature_states.count() == 1

    # When
    Environment.objects.create(name="New Environment", project=project)

    # Then
    # A new environment comes with a new feature state.
    feature.feature_states.count() == 2


def test_on_environment_update_feature_states(
    environment: Environment,
    feature: Feature,
) -> None:
    # When
    feature.default_enabled = True
    feature.save()
    environment.save()

    # Then
    assert FeatureState.objects.count() == 1


def test_environment_clone_does_not_modify_the_original_instance(
    environment: Environment,
) -> None:
    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert clone.name != environment.name
    assert clone.api_key != environment.api_key


def test_environment_clone_save_creates_feature_states(
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


def test_environment_clone_does_not_modify_source_feature_state(
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


def test_environment_clone_does_not_create_identities(
    environment: Environment,
):
    # Given
    Identity.objects.create(environment=environment, identifier="test_identity")

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert clone.identities.count() == 0


def test_environment_clone_clones_the_feature_states(
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature_state = feature.feature_states.first()
    assert feature_state.enabled is False

    # Enable the feature in the source environment
    feature_state.enabled = True
    feature_state.save()

    # When
    clone = environment.clone(name="Cloned env")

    # Then
    assert clone.feature_states.first().enabled is True


def test_environment_clone_clones_multivariate_feature_state_values(
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
def test_environment_get_from_cache_stores_environment_in_cache_on_success(
    mock_cache: MagicMock,
    environment: Environment,
) -> None:
    # Given
    mock_cache.get.return_value = None

    # When
    environment = Environment.get_from_cache(environment.api_key)

    # Then
    assert environment == environment
    mock_cache.set.assert_called_with(environment.api_key, environment, timeout=60)


def test_environment_get_from_cache_returns_None_if_no_matching_environment(
    environment: Environment,
) -> None:
    # Given
    api_key = "no-matching-env"

    # When
    env = Environment.get_from_cache(api_key)

    # Then
    assert env is None


def test_environment_get_from_cache_accepts_environment_api_key_model_key(
    environment: Environment,
) -> None:
    # Given
    api_key = EnvironmentAPIKey.objects.create(name="Some key", environment=environment)

    # When
    environment_from_cache = Environment.get_from_cache(api_key=api_key.key)

    # Then
    assert environment_from_cache == environment


def test_environment_get_from_cache_with_null_environment_key_returns_null(
    environment: Environment,
) -> None:
    # When
    environment2 = Environment.get_from_cache(None)

    # Then
    assert environment2 is None


@override_settings(
    CACHE_BAD_ENVIRONMENTS_SECONDS=60, CACHE_BAD_ENVIRONMENTS_AFTER_FAILURES=1
)
def test_environment_get_from_cache_does_not_hit_database_if_api_key_in_bad_env_cache(
    django_assert_num_queries: DjangoAssertNumQueries,
    db: None,
) -> None:
    # Given
    api_key = "bad-key"

    # When
    with django_assert_num_queries(1):
        [Environment.get_from_cache(api_key) for _ in range(10)]


def test_environment_api_key_model_is_valid_is_true_for_non_expired_active_key(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment,
            key="ser.random_key",
            name="test_key",
        ).is_valid
        is True
    )


def test_environment_api_key_model_is_valid_is_true_for_non_expired_active_key_with_expired_date_in_future(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment,
            key="ser.random_key",
            name="test_key",
            expires_at=timezone.now() + timedelta(days=5),
        ).is_valid
        is True
    )


def test_environment_api_key_model_is_valid_is_false_for_expired_active_key(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment,
            key="ser.random_key",
            name="test_key",
            expires_at=timezone.now() - timedelta(seconds=1),
        ).is_valid
        is False
    )


def test_environment_api_key_model_is_valid_is_false_for_non_expired_inactive_key(
    environment,
):
    assert (
        EnvironmentAPIKey.objects.create(
            environment=environment, key="ser.random_key", name="test_key", active=False
        ).is_valid
        is False
    )


def test_existence_of_multiple_environment_api_keys_does_not_break_get_from_cache(
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


def test_get_from_cache_sets_the_cache_correctly_with_environment_api_key(
    environment, environment_api_key, mocker
):
    # When
    returned_environment = Environment.get_from_cache(environment_api_key.key)

    # Then
    assert returned_environment == environment

    # and
    assert environment == environment_cache.get(environment_api_key.key)


def test_updated_at_gets_updated_when_environment_audit_log_created(environment):
    # When
    audit_log = AuditLog.objects.create(
        environment=environment, project=environment.project, log="random_audit_log"
    )

    # Then
    environment.refresh_from_db()
    assert environment.updated_at == audit_log.created_date


def test_updated_at_gets_updated_when_project_audit_log_created(environment):
    # When
    audit_log = AuditLog.objects.create(
        project=environment.project, log="random_audit_log"
    )
    environment.refresh_from_db()
    # Then
    assert environment.updated_at == audit_log.created_date


def test_change_request_audit_logs_does_not_update_updated_at(environment):
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


def test_save_environment_clears_environment_cache(mocker, project):
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
    mock_calls = mock_environment_cache.delete.mock_calls
    assert len(mock_calls) == 2
    assert mock_calls[0][1][0] == mock_calls[1][1][0] == old_key


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


def test_write_environments_to_dynamodb_project(
    dynamo_enabled_project,
    dynamo_enabled_project_environment_one,
    dynamo_enabled_project_environment_two,
    mock_dynamo_env_wrapper,
):
    # Given
    mock_dynamo_env_wrapper.reset_mock()

    # When
    Environment.write_environments_to_dynamodb(project_id=dynamo_enabled_project.id)

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
    dynamo_enabled_project.identity_overrides_v2_migration_status = (
        IdentityOverridesV2MigrationStatus.COMPLETE
    )
    dynamo_enabled_project.save()
    mock_dynamo_env_v2_wrapper.is_enabled = True

    # When
    Environment.write_environments_to_dynamodb(project_id=dynamo_enabled_project.id)

    # Then
    args, kwargs = mock_dynamo_env_v2_wrapper.write_environments.call_args
    assert kwargs == {}
    assert len(args) == 1
    assert_queryset_equal(
        args[0], Environment.objects.filter(project=dynamo_enabled_project)
    )


def test_write_environments_to_dynamodb__project_environments_v2_migrated__wrapper_disabled__wrapper_not_called(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamo_enabled_project_environment_two: Environment,
    mock_dynamo_env_wrapper: Mock,
    mock_dynamo_env_v2_wrapper: Mock,
) -> None:
    # Given
    mock_dynamo_env_v2_wrapper.is_enabled = False
    dynamo_enabled_project.identity_overrides_v2_migration_status = (
        IdentityOverridesV2MigrationStatus.COMPLETE
    )
    dynamo_enabled_project.save()

    # When
    Environment.write_environments_to_dynamodb(project_id=dynamo_enabled_project.id)

    # Then
    mock_dynamo_env_v2_wrapper.write_environments.assert_not_called()


@pytest.mark.parametrize(
    "identity_overrides_v2_migration_status",
    (
        IdentityOverridesV2MigrationStatus.NOT_STARTED,
        IdentityOverridesV2MigrationStatus.IN_PROGRESS,
    ),
)
def test_write_environments_to_dynamodb__project_environments_v2_not_migrated__wrapper_not_called(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    dynamo_enabled_project_environment_two: Environment,
    mock_dynamo_env_wrapper: Mock,
    mock_dynamo_env_v2_wrapper: Mock,
    identity_overrides_v2_migration_status: str,
) -> None:
    # Given
    dynamo_enabled_project.identity_overrides_v2_migration_status = (
        identity_overrides_v2_migration_status
    )
    dynamo_enabled_project.save()
    mock_dynamo_env_v2_wrapper.is_enabled = True

    # When
    Environment.write_environments_to_dynamodb(project_id=dynamo_enabled_project.id)

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
    with django_assert_num_queries(3):
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
    mocked_environment_document_cache.get.return_value = (
        map_environment_to_environment_document(environment)
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
    with django_assert_num_queries(3):
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
    assert not feature_state.get_feature_state_value()


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
def test_get_hide_disabled_flags(
    project, environment, environment_value, project_value, expected_result
):
    # Given
    project.hide_disabled_flags = project_value
    project.save()

    environment.hide_disabled_flags = environment_value
    environment.save()

    # Then
    assert environment.get_hide_disabled_flags() is expected_result


def test_saving_environment_api_key_creates_dynamo_document_if_enabled(
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


def test_deleting_environment_api_key_deletes_dynamo_document_if_enabled(
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


def test_deleting_environment_creates_task_to_delete_dynamo_document_if_enabled(
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


def test_delete_api_key_not_called_when_deleting_environment_api_key_for_non_edge_project(
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


def test_put_item_not_called_when_saving_environment_api_key_for_non_edge_project(
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


def test_delete_environment_with_committed_change_request(
    organisation: "Organisation",
    environment: Environment,
    change_request: "ChangeRequest",
    change_request_feature_state: FeatureState,
    django_user_model: typing.Type["Model"],
) -> None:
    # Given
    user = django_user_model.objects.create(email="test@example.com")
    user.add_organisation(organisation, OrganisationRole.ADMIN)
    change_request.approve(user)
    change_request.commit(user)

    # When
    environment.delete()

    # Then
    assert environment.deleted_at is not None


def test_create_environment_creates_feature_states_in_all_environments_and_environment_feature_version(
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
