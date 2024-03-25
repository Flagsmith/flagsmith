import json
from unittest import mock

from core.constants import INTEGER, STRING
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.identities.traits.constants import (
    TRAIT_STRING_VALUE_MAX_LENGTH,
)
from environments.identities.traits.models import Trait
from environments.identities.traits.views import TraitViewSet
from environments.models import Environment, EnvironmentAPIKey
from environments.permissions.constants import (
    MANAGE_IDENTITIES,
    VIEW_ENVIRONMENT,
    VIEW_IDENTITIES,
)
from environments.permissions.models import UserEnvironmentPermission
from environments.permissions.permissions import NestedEnvironmentPermissions
from organisations.models import Organisation
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from projects.permissions import VIEW_PROJECT


def test_can_set_trait_for_an_identity(
    api_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_key = "some-key"
    trait_value = "some-value"
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }

    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Trait.objects.filter(identity=identity, trait_key=trait_key).exists()


def test_cannot_set_trait_for_an_identity_for_organisations_without_persistence(
    api_client: APIClient,
    identity: Identity,
    organisation: Organisation,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_key = "some-key"
    trait_value = "some-value"
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }

    # an organisation that is configured to not store traits
    organisation.persist_trait_data = False
    organisation.save()
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # the request fails
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.data["detail"] == (
        "Organisation is not authorised to store traits."
    )

    # and no traits are stored
    assert Trait.objects.count() == 0


def test_can_set_trait_with_boolean_value_for_an_identity(
    api_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_key = "some-key"
    trait_value = True
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        Trait.objects.get(identity=identity, trait_key=trait_key).get_trait_value()
        == trait_value
    )


def test_can_set_trait_with_identity_value_for_an_identity(
    api_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_key = "some-key"
    trait_value = 12
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        Trait.objects.get(identity=identity, trait_key=trait_key).get_trait_value()
        == trait_value
    )


def test_can_set_trait_with_float_value_for_an_identity(
    api_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_key = "some-key"
    trait_value = 10.5
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    # and
    assert (
        Trait.objects.get(identity=identity, trait_key=trait_key).get_trait_value()
        == trait_value
    )


def test_add_trait_creates_identity_if_it_doesnt_exist(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    identifier = "new-identity"
    trait_key = "some-key"
    trait_value = 10.5
    data = {
        "identity": {"identifier": identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Identity.objects.filter(
        identifier=identifier, environment=environment
    ).exists()
    assert Trait.objects.filter(
        identity__identifier=identifier, trait_key=trait_key
    ).exists()


def test_trait_is_updated_if_already_exists(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_key = "some-key"
    trait_value = 10.5
    trait = Trait.objects.create(
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
        identity=identity,
    )
    new_value = "Some new value"
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": new_value,
    }

    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    # When
    api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    trait.refresh_from_db()
    assert trait.get_trait_value() == new_value


def test_increment_value_increments_trait_value_if_value_positive_integer(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    initial_value = 2
    increment_by = 2
    trait_key = "some-key"
    url = reverse("api-v1:sdk-traits-increment-value")
    trait = Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=INTEGER,
        integer_value=initial_value,
    )
    data = {
        "trait_key": trait_key,
        "identifier": identity.identifier,
        "increment_by": increment_by,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    trait.refresh_from_db()
    assert trait.get_trait_value() == initial_value + increment_by


def test_increment_value_decrements_trait_value_if_value_negative_integer(
    api_client: APIClient,
    identity: Identity,
    environment: Environment,
) -> None:
    # Given
    initial_value = 2
    increment_by = -2
    trait_key = "some-key"

    url = reverse("api-v1:sdk-traits-increment-value")
    trait = Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=INTEGER,
        integer_value=initial_value,
    )
    data = {
        "trait_key": trait_key,
        "identifier": identity.identifier,
        "increment_by": increment_by,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK

    trait.refresh_from_db()
    assert trait.get_trait_value() == initial_value + increment_by


def test_increment_value_initialises_trait_with_a_value_of_zero_if_it_doesnt_exist(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    increment_by = 1
    trait_key = "trait_key"
    url = reverse("api-v1:sdk-traits-increment-value")
    data = {
        "trait_key": trait_key,
        "identifier": identity.identifier,
        "increment_by": increment_by,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    api_client.post(url, data=data)

    # Then
    trait = Trait.objects.get(trait_key=trait_key, identity=identity)
    assert trait.get_trait_value() == increment_by


def test_increment_value_returns_400_if_trait_value_not_integer(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    trait_key = "trait_key"
    url = reverse("api-v1:sdk-traits-increment-value")
    Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=STRING,
        string_value="str",
    )
    data = {
        "trait_key": trait_key,
        "identifier": identity.identifier,
        "increment_by": 2,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    res = api_client.post(url, data=data)

    # Then
    assert res.status_code == status.HTTP_400_BAD_REQUEST


def test_set_trait_with_too_long_string_value_returns_400(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    trait_value = "t" * (TRAIT_STRING_VALUE_MAX_LENGTH + 1)
    trait_key = "trait_key"

    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }

    # When
    response = api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        f"Value string is too long. Must be less than {TRAIT_STRING_VALUE_MAX_LENGTH} character"
        == response.data["trait_value"][0]
    )


def test_can_set_trait_with_bad_value_for_an_identity(
    api_client: APIClient,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")

    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    trait_key = "trait_key"
    bad_trait_value = {"foo": "bar"}
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": bad_trait_value,
    }

    # When
    response = api_client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Trait.objects.get(
        identity=identity, trait_key=trait_key
    ).get_trait_value() == str(bad_trait_value)


def test_bulk_create_traits(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-bulk-create")
    trait_value = "trait_value"
    traits = [
        {
            "identity": {"identifier": "identifier1"},
            "trait_key": "trait_key1",
            "trait_value": trait_value,
        },
        {
            "identity": {"identifier": "identifier2"},
            "trait_key": "trait_key2",
            "trait_value": trait_value,
        },
    ]

    identifiers = [trait["identity"]["identifier"] for trait in traits]
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    # When
    response = api_client.put(
        url, data=json.dumps(traits), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Trait.objects.filter(identity__identifier__in=identifiers).count() == len(
        traits
    )


def test_bulk_create_traits_when_bad_trait_value_sent_then_trait_value_stringified(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-bulk-create")

    trait_value = "trait_value"
    traits = [
        {
            "identity": {"identifier": identity.identifier},
            "trait_key": "trait_key1",
            "trait_value": trait_value,
        },
        {
            "identity": {"identifier": identity.identifier},
            "trait_key": "trait_key2",
            "trait_value": trait_value,
        },
    ]
    # Add some bad data to test.
    bad_trait_key = "trait_999"
    bad_trait_value = {"foo": "bar"}
    traits.append(
        {
            "trait_value": bad_trait_value,
            "trait_key": bad_trait_key,
            "identity": {"identifier": identity.identifier},
        }
    )
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.put(
        url, data=json.dumps(traits), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Trait.objects.filter(identity=identity).count() == len(traits)
    assert Trait.objects.get(
        identity=identity, trait_key=bad_trait_key
    ).get_trait_value() == str(bad_trait_value)


def test_sending_null_value_in_bulk_create_deletes_trait_for_identity(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    trait_value = "trait_value"
    trait_key = "trait_key"
    url = reverse("api-v1:sdk-traits-bulk-create")
    trait_to_delete = Trait.objects.create(
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
        identity=identity,
    )
    trait_key_to_keep = "another_trait_key"
    trait_to_keep = Trait.objects.create(
        trait_key=trait_key_to_keep,
        value_type=STRING,
        string_value="value is irrelevant",
        identity=identity,
    )
    data = [
        {
            "identity": {"identifier": identity.identifier},
            "trait_key": trait_key,
            "trait_value": None,
        }
    ]
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then the request is successful
    assert response.status_code == status.HTTP_200_OK

    # and the trait is deleted
    assert not Trait.objects.filter(id=trait_to_delete.id).exists()

    # but the trait missing from the request is left untouched
    assert Trait.objects.filter(id=trait_to_keep.id).exists()


def test_bulk_create_traits_when_float_value_sent_then_trait_value_correct(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-bulk-create")
    traits = []

    # add float value trait
    float_trait_key = "float_key_999"
    float_trait_value = 45.88
    traits.append(
        {
            "trait_value": float_trait_value,
            "trait_key": float_trait_key,
            "identity": {"identifier": identity.identifier},
        }
    )
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.put(
        url, data=json.dumps(traits), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Trait.objects.filter(identity=identity).count() == 1
    assert (
        Trait.objects.get(
            identity=identity, trait_key=float_trait_key
        ).get_trait_value()
        == float_trait_value
    )


@override_settings(EDGE_API_URL="http://localhost")
@mock.patch("environments.identities.traits.views.forward_trait_request")
def test_post_trait_calls_forward_trait_request_with_correct_arguments(
    mocked_forward_trait_request: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    url = reverse("api-v1:sdk-traits-list")
    trait_key = "trait_key"
    trait_value = "trait_value"
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": trait_key,
        "trait_value": trait_value,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    api_client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    args, kwargs = mocked_forward_trait_request.delay.call_args_list[0]
    assert args == ()
    assert kwargs["args"][0] == "POST"
    assert kwargs["args"][1].get("X-Environment-Key") == environment.api_key
    assert kwargs["args"][2] == environment.project.id
    assert kwargs["args"][3] == data


@override_settings(EDGE_API_URL="http://localhost")
@mock.patch("environments.identities.traits.views.forward_trait_request")
def test_increment_value_calls_forward_trait_request_with_correct_arguments(
    mocked_forward_trait_request: mock.MagicMock,
    identity: Identity,
    api_client: APIClient,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    url = reverse("api-v1:sdk-traits-increment-value")
    trait_key = "trait_key"
    data = {
        "trait_key": trait_key,
        "identifier": identity.identifier,
        "increment_by": 1,
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    api_client.post(url, data=data)

    # Then
    args, kwargs = mocked_forward_trait_request.delay.call_args_list[0]
    assert args == ()
    assert kwargs["args"][0] == "POST"
    assert kwargs["args"][1].get("X-Environment-Key") == environment.api_key
    assert kwargs["args"][2] == project.id

    # And the structure of payload was correct.
    assert kwargs["args"][3]["identity"]["identifier"] == data["identifier"]
    assert kwargs["args"][3]["trait_key"] == data["trait_key"]
    assert kwargs["args"][3]["trait_value"]


@override_settings(EDGE_API_URL="http://localhost")
@mock.patch("environments.identities.traits.views.forward_trait_requests")
def test_bulk_create_traits_calls_forward_trait_request_with_correct_arguments(
    mocked_forward_trait_requests: mock.MagicMock,
    api_client: APIClient,
    environment: Environment,
    project: Project,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    url = reverse("api-v1:sdk-traits-bulk-create")
    data = [
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
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    api_client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    args, kwargs = mocked_forward_trait_requests.delay.call_args_list[0]
    assert args == ()
    assert kwargs["args"][0] == "PUT"
    assert kwargs["args"][1].get("X-Environment-Key") == environment.api_key
    assert kwargs["args"][2] == project.id
    assert kwargs["args"][3] == data


def test_create_trait_returns_403_if_client_cannot_set_traits(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": "foo",
        "trait_value": "bar",
    }
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    environment.allow_client_traits = False
    environment.save()

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {
        "non_field_errors": ["Setting traits not allowed with client key."]
    }


def test_server_key_can_create_trait_if_not_allow_client_traits(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-list")
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": "foo",
        "trait_value": "bar",
    }

    server_api_key = EnvironmentAPIKey.objects.create(environment=environment)
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=server_api_key.key)

    environment.allow_client_traits = False
    environment.save()

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_bulk_create_traits_returns_403_if_client_cannot_set_traits(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-bulk-create")
    data = [
        {
            "identity": {"identifier": identity.identifier},
            "trait_key": "foo",
            "trait_value": "bar",
        }
    ]
    environment.allow_client_traits = False
    environment.save()
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    # When
    response = api_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    # TODO: This bad request is in HTML form not JSON.
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_server_key_can_bulk_create_traits_if_not_allow_client_traits(
    identity: Identity,
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:sdk-traits-bulk-create")
    data = [
        {
            "identity": {"identifier": identity.identifier},
            "trait_key": "foo",
            "trait_value": "bar",
        }
    ]

    server_api_key = EnvironmentAPIKey.objects.create(environment=environment)
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=server_api_key.key)

    environment.allow_client_traits = False
    environment.save()

    # When
    response = api_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.data == data
    assert response.status_code == status.HTTP_200_OK


def test_delete_trait_only_deletes_single_trait_if_query_param_not_provided(
    identity: Identity,
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    trait_key = "trait_key"
    trait_value = "trait_value"
    identity_2 = Identity.objects.create(
        identifier="test-user-2", environment=environment
    )

    trait = Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )
    trait_2 = Trait.objects.create(
        identity=identity_2,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )

    url = reverse(
        "api-v1:environments:identities-traits-detail",
        args=[environment.api_key, identity.id, trait.id],
    )

    # When
    admin_client.delete(url)

    # Then
    assert not Trait.objects.filter(pk=trait.id).exists()
    assert Trait.objects.filter(pk=trait_2.id).exists()


def test_delete_trait_deletes_all_traits_if_query_param_provided(
    identity: Identity,
    environment: Environment,
    admin_client: APIClient,
) -> None:
    # Given
    trait_key = "trait_key"
    trait_value = "trait_value"
    identity_2 = Identity.objects.create(
        identifier="test-user-2", environment=environment
    )

    trait = Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )
    trait_2 = Trait.objects.create(
        identity=identity_2,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )

    base_url = reverse(
        "api-v1:environments:identities-traits-detail",
        args=[environment.api_key, identity.id, trait.id],
    )
    url = base_url + "?deleteAllMatchingTraits=true"

    # When
    admin_client.delete(url)

    # Then
    assert not Trait.objects.filter(pk=trait.id).exists()
    assert not Trait.objects.filter(pk=trait_2.id).exists()


def test_delete_trait_only_deletes_traits_in_current_environment(
    identity: Identity,
    environment: Environment,
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given
    environment_2 = Environment.objects.create(name="Test environment", project=project)
    trait_key = "trait_key"
    trait_value = "trait_value"
    identity_2 = Identity.objects.create(
        identifier="test-user-2", environment=environment_2
    )

    trait = Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )
    trait_2 = Trait.objects.create(
        identity=identity_2,
        trait_key=trait_key,
        value_type=STRING,
        string_value=trait_value,
    )

    base_url = reverse(
        "api-v1:environments:identities-traits-detail",
        args=[environment.api_key, identity.id, trait.id],
    )
    url = base_url + "?deleteAllMatchingTraits=true"

    # When
    admin_client.delete(url)

    # Then
    assert not Trait.objects.filter(pk=trait.id).exists()
    assert Trait.objects.filter(pk=trait_2.id).exists()


def test_set_trait_for_an_identity_is_not_throttled_by_user_throttle(
    settings, identity, environment, api_client
):
    # Given
    settings.REST_FRAMEWORK = {"DEFAULT_THROTTLE_RATES": {"user": "1/minute"}}

    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    url = reverse("api-v1:sdk-traits-list")
    data = {
        "identity": {"identifier": identity.identifier},
        "trait_key": "key",
        "trait_value": "value",
    }

    # When
    for _ in range(10):
        res = api_client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_200_OK


def test_user_with_manage_identities_permission_can_add_trait_for_identity(
    environment, identity, django_user_model, api_client
):
    # Given
    user = django_user_model.objects.create(email="user@example.com")
    api_client.force_authenticate(user)

    view_environment_permission = PermissionModel.objects.get(key=VIEW_ENVIRONMENT)
    manage_identities_permission = PermissionModel.objects.get(key=MANAGE_IDENTITIES)
    view_project_permission = PermissionModel.objects.get(key=VIEW_PROJECT)

    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=user, environment=environment
    )
    user_environment_permission.permissions.add(
        view_environment_permission, manage_identities_permission
    )

    user_project_permission = UserProjectPermission.objects.create(
        user=user, project=environment.project
    )
    user_project_permission.permissions.add(view_project_permission)

    url = reverse(
        "api-v1:environments:identities-traits-list",
        args=(environment.api_key, identity.id),
    )

    # When
    response = api_client.post(
        url, data={"trait_key": "foo", "value_type": "unicode", "string_value": "foo"}
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_trait_view_delete_trait(environment, admin_client, identity, trait, mocker):
    # Given
    url = reverse(
        "api-v1:environments:identities-traits-detail",
        args=(environment.api_key, identity.id, trait.id),
    )

    # When
    res = admin_client.delete(url)

    # Then
    assert res.status_code == status.HTTP_204_NO_CONTENT

    # and
    assert not Trait.objects.filter(pk=trait.id).exists()


def test_trait_view_set_update(environment, admin_client, identity, trait, mocker):
    # Given
    url = reverse(
        "api-v1:environments:identities-traits-detail",
        args=(environment.api_key, identity.id, trait.id),
    )
    new_value = "updated"

    # When
    response = admin_client.patch(url, data={"string_value": new_value})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["string_value"] == new_value


def test_edge_identity_view_set_get_permissions():
    # Given
    view_set = TraitViewSet()

    # When
    permissions = view_set.get_permissions()

    # Then
    assert isinstance(permissions[0], IsAuthenticated)
    assert isinstance(permissions[1], NestedEnvironmentPermissions)

    assert permissions[1].action_permission_map == {
        "list": VIEW_IDENTITIES,
        "retrieve": VIEW_IDENTITIES,
        "create": MANAGE_IDENTITIES,
        "update": MANAGE_IDENTITIES,
        "partial_update": MANAGE_IDENTITIES,
        "destroy": MANAGE_IDENTITIES,
    }
