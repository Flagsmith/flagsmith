import json

from edge_api.identities.mixins import (
    MigrateIdentitiesUsingRequestsMixin,
    MigrateTraitsUsingRequestMixin,
    _should_migrate,
)


def test_should_migrate_returns_false_if_identity_migration_is_not_already_done(
    mocker, settings
):
    # Given
    settings.EDGE_API_URL = "http//localhost"
    mocked_dynamo_wrapper = mocker.patch(
        "edge_api.identities.mixins.DynamoIdentityWrapper"
    )
    mocked_dynamo_wrapper.return_value.is_migration_done.return_value = False
    project_id = 1

    # When
    result = _should_migrate(project_id)
    # Then
    assert result is False
    mocked_dynamo_wrapper.assert_called_with()
    mocked_dynamo_wrapper.return_value.is_migration_done.assert_called_with(project_id)


def test_should_migrate_returns_false_if_edge_api_url_is_not_set(mocker, settings):
    # Given
    settings.EDGE_API_URL = ""
    # When
    result = _should_migrate(1)
    # Then
    assert result is False


def test_should_migrate_returns_true_if_identity_migration_is_done(mocker, settings):
    # Given
    settings.EDGE_API_URL = "http//localhost"
    mocked_dynamo_wrapper = mocker.patch(
        "edge_api.identities.mixins.DynamoIdentityWrapper"
    )
    mocked_dynamo_wrapper.return_value.is_migration_done.return_value = True
    project_id = 1

    # When
    result = _should_migrate(project_id)
    # Then
    assert result is True
    mocked_dynamo_wrapper.assert_called_with()
    mocked_dynamo_wrapper.return_value.is_migration_done.assert_called_with(project_id)


def test_migrate_identity_calls_async_function_with_correct_arguments(
    mocker, rf, environment
):
    # Given
    request = rf.get("/identities")
    mixin_obj = MigrateIdentitiesUsingRequestsMixin()
    migrate_identity_async = mocker.patch.object(mixin_obj, "_migrate_identity_async")
    # When

    mixin_obj.migrate_identity(request, environment)

    # Then
    migrate_identity_async.assert_called_with(request, environment)


def test_migrate_identity_sync_for_get_makes_correct_get_request(
    mocker, rf, environment
):

    # Given
    identities_url = "http//localhost/identities/"
    query_params = {"identifier": "test_123"}
    request = rf.get("/identities", query_params)

    mocked_should_migrate = mocker.patch(
        "edge_api.identities.mixins._should_migrate",
        return_value=True,
    )

    mocker.patch(
        "edge_api.identities.mixins.MigrateIdentitiesUsingRequestsMixin.identities_url",
        identities_url,
    )

    mocked_requests = mocker.patch("edge_api.identities.mixins.requests")

    # When
    MigrateIdentitiesUsingRequestsMixin()._migrate_identity_sync(request, environment)

    # Then
    mocked_should_migrate.assert_called_with(environment.project.id)
    args, kwargs = mocked_requests.get.call_args
    assert args[0] == identities_url
    assert kwargs["params"] == query_params
    assert kwargs["headers"]["X-Environment-Key"] == environment.api_key
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_migrate_identity_sync_for_post_request_makes_correct_post_request(
    mocker, rf, environment
):
    # Given
    identities_url = "http//localhost/identities/"
    request_data = {"key": "value"}
    request = rf.post("/identities")
    request.data = request_data
    mocked_should_migrate = mocker.patch(
        "edge_api.identities.mixins._should_migrate",
        return_value=True,
    )

    mocker.patch(
        "edge_api.identities.mixins.MigrateIdentitiesUsingRequestsMixin.identities_url",
        identities_url,
    )

    mocked_requests = mocker.patch("edge_api.identities.mixins.requests")

    # When
    MigrateIdentitiesUsingRequestsMixin()._migrate_identity_sync(request, environment)

    # Then
    mocked_should_migrate.assert_called_with(environment.project.id)
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == identities_url
    assert kwargs["data"] == json.dumps(request_data)
    assert kwargs["headers"]["X-Environment-Key"] == environment.api_key
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_migrate_trait_calls_async_function_with_correct_arguments(
    mocker, rf, environment
):
    # Given
    request = rf.get("/traits")
    mixin_obj = MigrateTraitsUsingRequestMixin()
    migrate_trait_async = mocker.patch.object(mixin_obj, "_migrate_trait_async")

    # When
    mixin_obj.migrate_trait(request, environment)

    # Then
    migrate_trait_async.assert_called_with(request, environment, None)


def test_migrate_trait_bulk_calls_async_function_with_correct_arguments(
    mocker, rf, environment
):
    # Given
    request = rf.get("/traits")
    mixin_obj = MigrateTraitsUsingRequestMixin()
    migrate_trait_bulk_async = mocker.patch.object(
        mixin_obj, "_migrate_trait_bulk_async"
    )

    # When
    mixin_obj.migrate_trait_bulk(request, environment)

    # Then
    migrate_trait_bulk_async.assert_called_with(request, environment)


def test_migrate_trait_sync_makes_correct_post_request_when_payload_is_none(
    mocker, rf, environment
):
    # Given
    request_data = {
        "identity": {"identifier": "test_user_123"},
        "trait_key": "key",
        "trait_value": "value",
    }
    request = rf.post("/traits")
    request.data = request_data

    traits_url = "http://localhost/traits"
    mocker.patch(
        "edge_api.identities.mixins.MigrateTraitsUsingRequestMixin.traits_url",
        traits_url,
    )

    mocked_requests = mocker.patch("edge_api.identities.mixins.requests")
    mocked_should_migrate = mocker.patch(
        "edge_api.identities.mixins._should_migrate",
        return_value=True,
    )

    # When
    MigrateTraitsUsingRequestMixin()._migrate_trait_sync(
        request, environment, payload=None
    )

    # Then
    mocked_should_migrate.assert_called_with(environment.project.id)
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == traits_url
    assert kwargs["data"] == json.dumps(request_data)
    assert kwargs["headers"]["X-Environment-Key"] == environment.api_key
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_migrate_trait_sync_post_request_uses_payload_over_request_data_if_not_none(
    mocker, rf, environment
):
    # Given
    payload = {
        "identity": {"identifier": "test_user_123"},
        "trait_key": "key",
        "trait_value": "value",
    }
    request_data = {"key": "value"}
    request = rf.post("/traits")
    request.data = request_data

    traits_url = "http://localhost/traits"
    mocker.patch(
        "edge_api.identities.mixins.MigrateTraitsUsingRequestMixin.traits_url",
        traits_url,
    )

    mocked_requests = mocker.patch("edge_api.identities.mixins.requests")
    mocked_should_migrate = mocker.patch(
        "edge_api.identities.mixins._should_migrate",
        return_value=True,
    )

    # When
    MigrateTraitsUsingRequestMixin()._migrate_trait_sync(
        request, environment, payload=payload
    )

    # Then
    mocked_should_migrate.assert_called_with(environment.project.id)
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == traits_url
    assert kwargs["data"] == json.dumps(payload)
    assert kwargs["headers"]["X-Environment-Key"] == environment.api_key
    assert kwargs["headers"]["Content-Type"] == "application/json"


def test_migrate_trait_sync_bulk_calls_migrate_trait_sync_with_correct_arguments(
    mocker, rf, environment
):
    # Given
    request_data = [
        {
            "identity": {"identifier": "test_user_123"},
            "trait_key": "key",
            "trait_value": "value",
        },
        {
            "identity": {"identifier": "test_user_123"},
            "trait_key": "key1",
            "trait_value": "value1",
        },
    ]
    request = rf.post("/traits")
    request.data = request_data

    mocked_migrate_trait_sync = mocker.patch(
        "edge_api.identities.mixins.MigrateTraitsUsingRequestMixin._migrate_trait_sync",
    )

    # When
    MigrateTraitsUsingRequestMixin()._migrate_trait_bulk_sync(request, environment)

    # Then
    mocked_migrate_trait_sync.assert_any_call(request, environment, request_data[0])
    mocked_migrate_trait_sync.assert_any_call(request, environment, request_data[1])
    assert mocked_migrate_trait_sync.call_count == 2
