import json

import pytest
from common.environments.permissions import (
    TAG_SUPPORTED_PERMISSIONS,
    VIEW_ENVIRONMENT,
)
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from flag_engine.segments.constants import EQUAL
from pytest_django import DjangoAssertNumQueries
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from api_keys.models import MasterAPIKey
from audit.models import AuditLog, RelatedObjectType  # type: ignore[attr-defined]
from core.constants import STRING
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment, EnvironmentAPIKey, Webhook
from environments.permissions.models import UserEnvironmentPermission
from features.models import Feature, FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from metadata.models import Metadata, MetadataModelField
from organisations.models import Organisation
from permissions.models import PermissionModel
from projects.models import Project, UserProjectPermission
from segments.models import Condition, Segment, SegmentRule
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser


def test_retrieve_environment(
    admin_client_new: APIClient, environment: Environment
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    assert response_json["id"] == environment.id
    assert response_json["name"] == environment.name
    assert response_json["project"] == environment.project_id
    assert response_json["api_key"] == environment.api_key
    assert response_json["allow_client_traits"] == environment.allow_client_traits
    assert response_json["banner_colour"] == environment.banner_colour
    assert response_json["banner_text"] == environment.banner_text
    assert response_json["description"] == environment.description
    assert response_json["hide_disabled_flags"] == environment.hide_disabled_flags
    assert response_json["hide_sensitive_data"] == environment.hide_sensitive_data
    assert response_json["metadata"] == []
    assert (
        response_json["minimum_change_request_approvals"]
        == environment.minimum_change_request_approvals
    )
    assert (
        response_json["total_segment_overrides"] == environment.feature_segments.count()
    )
    assert (
        response_json["use_identity_composite_key_for_hashing"]
        == environment.use_identity_composite_key_for_hashing
    )
    assert (
        response_json["use_mv_v2_evaluation"]
        == environment.use_identity_composite_key_for_hashing
    )


def test_get_by_uuid_returns_environment(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    url = reverse(
        "api-v1:environments:environment-get-by-uuid",
        args=[environment.uuid],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(environment.uuid)


def test_get_by_uuid_returns_403_for_user_without_permission(
    staff_client: APIClient, environment: Environment
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-get-by-uuid",
        args=[environment.uuid],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_with_view_environment_permission_can_retrieve_environment(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])

    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_can_clone_environment_with_create_environment_permission(
    staff_client: APIClient,
    environment: Environment,
    user_project_permission: UserProjectPermission,
    create_environment_permission: PermissionModel,
) -> None:
    # Given
    env_name = "Cloned env"
    user_project_permission.permissions.add(create_environment_permission)

    url = reverse("api-v1:environments:environment-clone", args=[environment.api_key])

    # When
    response = staff_client.post(url, {"name": env_name})

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_should_return_identities_for_an_environment(
    admin_client_new: APIClient,
    environment: Environment,
    identity: Identity,
) -> None:
    # Given
    identifier_two = "user2"
    Identity.objects.create(identifier=identifier_two, environment=environment)
    url = reverse(
        "api-v1:environments:environment-identities-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.data["results"][0]["identifier"] == identity.identifier
    assert response.data["results"][1]["identifier"] == identifier_two


def test_audit_log_entry_created_when_new_environment_created(
    project: Project,
    admin_client_new: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-list")
    data = {"project": project.id, "name": "Test Environment"}

    # When
    admin_client_new.post(url, data=data)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.ENVIRONMENT.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client, master_api_key, author",
    [
        (
            lazy_fixture("admin_master_api_key_client"),
            lazy_fixture("admin_master_api_key_object"),
            None,
        ),
        (lazy_fixture("admin_client_original"), None, lazy_fixture("admin_user")),
    ],
)
def test_audit_log_created_when_feature_state_updated(
    feature: Feature,
    environment: Environment,
    client: APIClient,
    master_api_key: MasterAPIKey,
    author: FFAdminUser,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(feature=feature, environment=environment)
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )
    data = {"id": feature.id, "enabled": True}

    # When
    client.put(url, data=data)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE_STATE.name
        ).count()
        == 1
    )
    assert AuditLog.objects.first().author == author
    assert AuditLog.objects.first().master_api_key == master_api_key


def test_delete_trait_keys_deletes_trait_for_all_users_in_that_environment(
    environment: Environment,
    identity: Identity,
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    environment2 = Environment.objects.create(
        project=project, name="Test Environment 2"
    )

    identity2 = Identity.objects.create(
        environment=environment2, identifier="identity2"
    )

    trait_key = "trait-key"
    Trait.objects.create(
        identity=identity,
        trait_key=trait_key,
        string_value="blah",
        value_type=STRING,
    )
    Trait.objects.create(
        identity=identity2,
        trait_key=trait_key,
        string_value="blah",
        value_type=STRING,
    )

    url = reverse(
        "api-v1:environments:environment-delete-traits",
        args=[environment.api_key],
    )

    # When
    response = admin_client_new.post(url, data={"key": trait_key})

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert not Trait.objects.filter(identity=identity, trait_key=trait_key).exists()
    assert Trait.objects.filter(identity=identity2, trait_key=trait_key).exists()


def test_environment_user_can_get_their_permissions(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:environment-my-permissions", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not response.json()["admin"]
    assert "VIEW_ENVIRONMENT" in response.json()["permissions"]


def test_environment_user_can_get_their_detailed_permissions(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    staff_user: FFAdminUser,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:environment-user-detailed-permissions",
        args=[environment.api_key, staff_user.id],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["admin"] is False
    assert response.json()["is_directly_granted"] is False
    assert response.json()["derived_from"] == {"groups": [], "roles": []}
    assert response.json()["permissions"] == [
        {
            "permission_key": "VIEW_ENVIRONMENT",
            "is_directly_granted": True,
            "derived_from": {"groups": [], "roles": []},
        }
    ]


def test_environment_user_can_not_get_detailed_permissions_of_other_user(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    admin_user: FFAdminUser,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:environment-user-detailed-permissions",
        args=[environment.api_key, admin_user.id],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_environment_admin_can_get_detailed_permissions_of_other_user(
    admin_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:environment-user-detailed-permissions",
        args=[environment.api_key, staff_user.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["admin"] is False
    assert response.json()["is_directly_granted"] is False
    assert response.json()["derived_from"] == {"groups": [], "roles": []}
    assert response.json()["permissions"] == [
        {
            "permission_key": "VIEW_ENVIRONMENT",
            "is_directly_granted": True,
            "derived_from": {"groups": [], "roles": []},
        }
    ]


def test_can_create_webhook_for_an_environment(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    url = reverse(
        "api-v1:environments:environment-webhooks-list",
        args=[environment.api_key],
    )
    data = {"url": valid_webhook_url, "enabled": True}

    # When
    response = admin_client_new.post(url, data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert Webhook.objects.filter(environment=environment, **data).exists()


def test_can_update_webhook_for_an_environment(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    webhook = Webhook.objects.create(url=valid_webhook_url, environment=environment)
    url = reverse(
        "api-v1:environments:environment-webhooks-detail",
        args=[environment.api_key, webhook.id],
    )
    data = {"url": "http://my.new.url.com/wehbooks", "enabled": False}

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    webhook.refresh_from_db()
    assert webhook.url == data["url"] and not webhook.enabled


def test_can_update_webhook_secret(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    webhook = Webhook.objects.create(url=valid_webhook_url, environment=environment)
    url = reverse(
        "api-v1:environments:environment-webhooks-detail",
        args=[environment.api_key, webhook.id],
    )
    data = {"secret": "random_secret"}

    # When
    response = admin_client_new.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    webhook.refresh_from_db()
    assert webhook.secret == data["secret"]


def test_can_delete_webhook_for_an_environment(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    webhook = Webhook.objects.create(url=valid_webhook_url, environment=environment)
    url = reverse(
        "api-v1:environments:environment-webhooks-detail",
        args=[environment.api_key, webhook.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Webhook.objects.filter(id=webhook.id).exists()


def test_can_list_webhooks_for_an_environment(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    webhook = Webhook.objects.create(url=valid_webhook_url, environment=environment)
    url = reverse(
        "api-v1:environments:environment-webhooks-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["id"] == webhook.id


def test_cannot_delete_webhooks_for_environment_user_does_not_belong_to(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    valid_webhook_url = "http://my.webhook.com/webhooks"
    new_organisation = Organisation.objects.create(name="New organisation")
    new_project = Project.objects.create(
        name="New project", organisation=new_organisation
    )
    new_environment = Environment.objects.create(
        name="New Environment", project=new_project
    )
    webhook = Webhook.objects.create(url=valid_webhook_url, environment=new_environment)
    url = reverse(
        "api-v1:environments:environment-webhooks-detail",
        args=[environment.api_key, webhook.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert Webhook.objects.filter(id=webhook.id).exists()


def test_list_api_keys(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    api_key_1 = EnvironmentAPIKey.objects.create(
        environment=environment, name="api key 1"
    )
    api_key_2 = EnvironmentAPIKey.objects.create(
        environment=environment, name="api key 2"
    )
    url = reverse("api-v1:environments:api-keys-list", args={environment.api_key})  # type: ignore[arg-type]

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json) == 2

    assert {api_key["id"] for api_key in response_json} == {
        api_key_1.id,
        api_key_2.id,
    }


def test_create_api_key(
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
    some_key = "some.key"
    data = {"name": "Some key", "key": some_key}
    url = reverse("api-v1:environments:api-keys-list", args={environment.api_key})  # type: ignore[arg-type]

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    assert response.data["key"] and response.data["key"].startswith("ser.")
    assert response.data["key"] != some_key
    assert response.data["active"] is True


def test_update_api_key(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    old_name = "Some key"
    api_key = EnvironmentAPIKey.objects.create(name=old_name, environment=environment)
    update_url = reverse(
        "api-v1:environments:api-keys-detail",
        args=[environment.api_key, api_key.id],
    )

    # When
    new_name = "new name"
    new_key = "new_key"
    response = admin_client_new.patch(
        update_url, data={"active": False, "name": new_name, "key": new_key}
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    api_key.refresh_from_db()
    assert api_key.name == new_name
    assert not api_key.active
    assert api_key.key != new_key


def test_delete_api_key(
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    api_key = EnvironmentAPIKey.objects.create(name="Some key", environment=environment)

    delete_url = reverse(
        "api-v1:environments:api-keys-detail",
        args=[environment.api_key, api_key.id],
    )

    # When
    admin_client_new.delete(delete_url)

    # Then
    assert not EnvironmentAPIKey.objects.filter(id=api_key.id)


@pytest.mark.parametrize(
    "client, is_admin_master_api_key_client",
    [
        (lazy_fixture("admin_master_api_key_client"), True),
        (lazy_fixture("admin_client_original"), False),
    ],
)
def test_should_create_environments(  # type: ignore[no-untyped-def]
    project, client, admin_user, is_admin_master_api_key_client
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-list")
    description = "This is the description"
    data = {
        "name": "Test environment",
        "project": project.id,
        "description": description,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["description"] == description
    assert response.json()["use_mv_v2_evaluation"] is True
    assert response.json()["use_identity_overrides_in_local_eval"] is True
    assert response.json()["use_identity_composite_key_for_hashing"] is True

    # and user is admin
    if not is_admin_master_api_key_client:
        assert UserEnvironmentPermission.objects.filter(
            user=admin_user, admin=True, environment__id=response.json()["id"]
        ).exists()


def test_environment_matches_existing_environment_name(
    project: Project,
    admin_client: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-list")
    description = "This is the description"
    name = "Test environment"
    data = {
        "name": name,
        "project": project.id,
        "description": description,
    }
    Environment.objects.create(name=name, description=description, project=project)

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "non_field_errors": ["An environment with this name already exists."]
    }


def test_create_environment_without_required_metadata_returns_400(  # type: ignore[no-untyped-def]
    project,
    admin_client_new,
    required_a_environment_metadata_field,
    optional_b_environment_metadata_field,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-list")
    description = "This is the description"
    data = {
        "name": "Test environment",
        "project": project.id,
        "description": description,
    }

    # When
    response = admin_client_new.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Missing required metadata field" in response.json()["metadata"][0]


@pytest.mark.skipif(
    settings.IS_RBAC_INSTALLED is True,
    reason="Skip this test if RBAC is installed",
)
def test_view_environment_with_staff__query_count_is_expected_without_rbac(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    project: Project,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment_metadata_a: Metadata,
    environment_metadata_b: Metadata,
    required_a_environment_metadata_field: MetadataModelField,
    environment_content_type: ContentType,
) -> None:
    _assert_view_environment_with_staff__query_count(
        staff_client,
        environment,
        with_environment_permissions,
        project,
        django_assert_num_queries,
        environment_metadata_a,
        environment_metadata_b,
        required_a_environment_metadata_field,
        environment_content_type,
        expected_query_count=9,
    )


@pytest.mark.skipif(
    settings.IS_RBAC_INSTALLED is False,
    reason="Skip this test if RBAC is not installed",
)
def test_view_environment_with_staff__query_count_is_expected_with_rbac(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    project: Project,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment_metadata_a: Metadata,
    environment_metadata_b: Metadata,
    required_a_environment_metadata_field: MetadataModelField,
    environment_content_type: ContentType,
) -> None:  # pragma: no cover
    _assert_view_environment_with_staff__query_count(
        staff_client,
        environment,
        with_environment_permissions,
        project,
        django_assert_num_queries,
        environment_metadata_a,
        environment_metadata_b,
        required_a_environment_metadata_field,
        environment_content_type,
        expected_query_count=10,
    )


def _assert_view_environment_with_staff__query_count(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    project: Project,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment_metadata_a: Metadata,
    environment_metadata_b: Metadata,
    required_a_environment_metadata_field: MetadataModelField,
    environment_content_type: ContentType,
    expected_query_count: int,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    url = reverse("api-v1:environments:environment-list")
    data = {"project": project.id}

    # When
    with django_assert_num_queries(expected_query_count):
        response = staff_client.get(url, data=data, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK

    # Add an environment to make sure the query count is the same.
    environment_2 = Environment.objects.create(
        name="Second Environment", project=project
    )
    Metadata.objects.create(
        object_id=environment_2.id,
        content_type=environment_content_type,
        model_field=required_a_environment_metadata_field,
        field_value="10",
    )

    with_environment_permissions([VIEW_ENVIRONMENT], environment_id=environment_2.id)  # type: ignore[call-arg]

    # One additional query for an unrelated, unfixable N+1 issue that deals with
    # the defer logic around filtered environments.
    expected_query_count += 1

    # Then
    with django_assert_num_queries(expected_query_count):
        response = staff_client.get(url, data=data, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK


def test_view_environment_with_admin__query_count_is_expected(
    admin_client_new: APIClient,
    environment: Environment,
    project: Project,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment_metadata_a: Metadata,
    environment_metadata_b: Metadata,
    required_a_environment_metadata_field: MetadataModelField,
    environment_content_type: ContentType,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-list")
    data = {"project": project.id}
    expected_query_count = 5

    # When
    with django_assert_num_queries(expected_query_count):
        response = admin_client_new.get(url, data=data, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK

    # Add an environment to make sure the query count is the same.
    environment_2 = Environment.objects.create(
        name="Second Environment", project=project
    )
    Metadata.objects.create(
        object_id=environment_2.id,
        content_type=environment_content_type,
        model_field=required_a_environment_metadata_field,
        field_value="10",
    )

    # Then
    with django_assert_num_queries(expected_query_count):
        response = admin_client_new.get(url, data=data, content_type="application/json")

    assert response.status_code == status.HTTP_200_OK


def test_create_environment_with_required_metadata_returns_201(  # type: ignore[no-untyped-def]
    project,
    admin_client_new,
    required_a_environment_metadata_field,
    optional_b_environment_metadata_field,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-list")
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test environment",
        "project": project.id,
        "description": description,
        "metadata": [
            {
                "model_field": required_a_environment_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == required_a_environment_metadata_field.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


def test_update_environment_metadata(  # type: ignore[no-untyped-def]
    project,
    admin_client_new,
    environment,
    environment_metadata_a,
    environment_metadata_b,
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])
    updated_field_value = 999

    # Update metadata for field a (environment_metadata_a) and remove metadata for field b
    data = {
        "project": project.id,
        "name": "New name",
        "description": "new_data",
        "metadata": [
            {
                "model_field": environment_metadata_a.model_field.id,
                "field_value": updated_field_value,
                "id": environment_metadata_a.id,
            },
        ],
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["metadata"]) == 1
    assert list(environment.metadata.values("model_field_id", "field_value")) == [
        {
            "model_field_id": environment_metadata_a.model_field.id,
            "field_value": str(updated_field_value),
        }
    ]


def test_create_multiple_environments_with_metadata_keeps_metadata_isolated(
    project: Project,
    admin_client_new: APIClient,
    optional_b_environment_metadata_field: MetadataModelField,
) -> None:
    """
    Test that creating multiple environments with metadata keeps metadata properly isolated.
    This is a regression test for the bug where creating a second environment would remove
    metadata from the first environment if the user sent the first environment's metadata ID.
    """
    # Given
    url = reverse("api-v1:environments:environment-list")

    # Create first environment with metadata
    first_environment_data = {
        "name": "First Environment",
        "project": project.id,
        "description": "First environment description",
        "metadata": [
            {
                "model_field": optional_b_environment_metadata_field.id,
                "field_value": "100",
            },
        ],
    }

    # When - Create first environment
    first_response = admin_client_new.post(
        url, data=json.dumps(first_environment_data), content_type="application/json"
    )

    # Then - First environment should be created successfully
    assert first_response.status_code == status.HTTP_201_CREATED
    first_environment_api_key = first_response.json()["api_key"]
    first_metadata = first_response.json()["metadata"]
    assert len(first_metadata) == 1
    assert first_metadata[0]["field_value"] == "100"
    first_metadata_id = first_metadata[0]["id"]

    # Given - Create second environment
    second_environment_data = {
        "name": "Second Environment",
        "project": project.id,
        "description": "Second environment description",
        "metadata": [
            {
                "id": first_metadata_id,  # user mistakenly sends existing metadata ID
                "model_field": optional_b_environment_metadata_field.id,
                "field_value": "200",
            },
        ],
    }

    # When - Create second environment
    second_response = admin_client_new.post(
        url, data=json.dumps(second_environment_data), content_type="application/json"
    )

    # Then - Second environment should be created successfully
    assert second_response.status_code == status.HTTP_201_CREATED
    second_environment_api_key = second_response.json()["api_key"]
    second_metadata = second_response.json()["metadata"]
    assert len(second_metadata) == 1
    assert second_metadata[0]["field_value"] == "200"
    # The metadata ID should be different (new metadata instance created)
    assert second_metadata[0]["id"] != first_metadata_id

    # When - Retrieve first environment to verify metadata is still there
    first_environment_url = reverse(
        "api-v1:environments:environment-detail", args=[first_environment_api_key]
    )
    first_environment_check = admin_client_new.get(first_environment_url)

    # Then - First environment should still have its metadata
    assert first_environment_check.status_code == status.HTTP_200_OK
    first_environment_metadata_after = first_environment_check.json()["metadata"]
    assert len(first_environment_metadata_after) == 1
    assert first_environment_metadata_after[0]["field_value"] == "100"
    assert first_environment_metadata_after[0]["id"] == first_metadata_id

    # When - Retrieve second environment to verify metadata
    second_environment_url = reverse(
        "api-v1:environments:environment-detail", args=[second_environment_api_key]
    )
    second_environment_check = admin_client_new.get(second_environment_url)

    # Then - Second environment should have its own metadata
    assert second_environment_check.status_code == status.HTTP_200_OK
    second_environment_metadata_after = second_environment_check.json()["metadata"]
    assert len(second_environment_metadata_after) == 1
    assert second_environment_metadata_after[0]["field_value"] == "200"
    assert second_environment_metadata_after[0]["id"] != first_metadata_id


def test_audit_log_entry_created_when_environment_updated(
    environment: Environment, project: Project, admin_client_new: APIClient
) -> None:
    # Given
    environment = Environment.objects.create(name="Test environment", project=project)
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])
    banner_text = "production environment be careful"
    banner_colour = "#FF0000"
    hide_disabled_flags = True
    use_identity_composite_key_for_hashing = True
    use_identity_overrides_in_local_eval = True
    hide_sensitive_data = True

    data = {
        "project": project.id,
        "name": "New name",
        "banner_text": banner_text,
        "banner_colour": banner_colour,
        "hide_disabled_flags": hide_disabled_flags,
        "use_identity_composite_key_for_hashing": use_identity_composite_key_for_hashing,
        "use_identity_overrides_in_local_eval": use_identity_overrides_in_local_eval,
        "hide_sensitive_data": hide_sensitive_data,
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.ENVIRONMENT.name
        ).count()
        == 1
    )
    assert response.json()["banner_text"] == banner_text
    assert response.json()["banner_colour"] == banner_colour
    assert response.json()["hide_disabled_flags"] == hide_disabled_flags
    assert response.json()["hide_sensitive_data"] == hide_sensitive_data
    assert (
        response.json()["use_identity_overrides_in_local_eval"]
        == use_identity_overrides_in_local_eval
    )
    assert (
        response.json()["use_identity_composite_key_for_hashing"]
        == use_identity_composite_key_for_hashing
    )


def test_environment_update_cannot_change_is_creating(
    environment: Environment, project: Project, admin_client_new: APIClient
) -> None:
    # Given
    environment = Environment.objects.create(name="Test environment", project=project)
    assert environment.is_creating is False
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])

    data = {
        "project": project.id,
        "name": "New name",
        "is_creating": True,
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_creating"] is False


def test_get_document(
    environment: Environment,
    project: Project,
    staff_client: APIClient,
    feature: Feature,
    segment: Segment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    # and some sample data to make sure we're testing all of the document
    segment_rule = SegmentRule.objects.create(
        segment=segment, type=SegmentRule.ALL_RULE
    )
    Condition.objects.create(
        operator=EQUAL, property="property", value="value", rule=segment_rule
    )

    # and the relevant URL to get an environment document
    url = reverse(
        "api-v1:environments:environment-get-document", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()


def test_cannot_get_environment_document_without_permission(
    staff_client: APIClient, environment: Environment
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-get-document", args=[environment.api_key]
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_all_trait_keys_for_environment_only_returns_distinct_keys(
    identity: Identity,
    admin_client_new: APIClient,
    trait: Trait,
    environment: Environment,
) -> None:
    # Given
    trait_key_one = trait.trait_key
    trait_key_two = "trait-key-two"

    identity_two = Identity.objects.create(
        environment=environment, identifier="identity-two"
    )

    Trait.objects.create(
        identity=identity,
        trait_key=trait_key_two,
        string_value="blah",
        value_type=STRING,
    )
    Trait.objects.create(
        identity=identity_two,
        trait_key=trait_key_one,
        string_value="blah",
        value_type=STRING,
    )

    url = reverse(
        "api-v1:environments:environment-trait-keys", args=[environment.api_key]
    )

    # When
    res = admin_client_new.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK

    # and - only distinct keys are returned
    assert len(res.json().get("keys")) == 2


def test_user_with_view_environment_can_get_trait_keys(
    identity: Identity,
    staff_client: APIClient,
    trait: Trait,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-trait-keys", args=[environment.api_key]
    )

    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    # When
    res = staff_client.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK


def test_delete_trait_keys_deletes_traits_matching_provided_key_only(
    identity: Identity,
    admin_client_new: APIClient,
    trait: Trait,
    environment: Environment,
) -> None:
    # Given
    trait_to_delete = trait.trait_key
    trait_to_persist = "trait-key-to-persist"
    Trait.objects.create(
        identity=identity,
        trait_key=trait_to_persist,
        value_type=STRING,
        string_value="blah",
    )

    url = reverse(
        "api-v1:environments:environment-delete-traits", args=[environment.api_key]
    )

    # When
    admin_client_new.post(url, data={"key": trait_to_delete})

    # Then
    assert not Trait.objects.filter(
        identity=identity, trait_key=trait_to_delete
    ).exists()

    # and
    assert Trait.objects.filter(identity=identity, trait_key=trait_to_persist).exists()


def test_user_can_list_environment_permission(
    admin_client_new: APIClient, environment: Environment
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-permissions")

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 7

    returned_supported_permissions = [
        permission["key"]
        for permission in response.json()
        if permission["supports_tag"] is True
    ]
    assert set(returned_supported_permissions) == set(TAG_SUPPORTED_PERMISSIONS)


def test_environment_my_permissions_reruns_400_for_master_api_key(
    admin_master_api_key_client: APIClient, environment: Environment
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-my-permissions", args=[environment.api_key]
    )

    # When
    response = admin_master_api_key_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["detail"]
        == "This endpoint can only be used with a user and not Master API Key"
    )


def test_partial_environment_update(
    admin_client: APIClient, environment: "Environment"
) -> None:
    # Given
    url = reverse("api-v1:environments:environment-detail", args=[environment.api_key])
    new_name = "updated!"

    # When
    response = admin_client.patch(
        url, data=json.dumps({"name": new_name}), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_cannot_enable_v2_versioning_for_environment_already_enabled(
    environment_v2_versioning: Environment,
    admin_client_new: APIClient,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-enable-v2-versioning",
        args=[environment_v2_versioning.api_key],
    )

    mock_enable_v2_versioning = mocker.patch("environments.views.enable_v2_versioning")

    # When
    response = admin_client_new.post(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Environment already using v2 versioning."}

    mock_enable_v2_versioning.delay.assert_not_called()


def test_total_segment_overrides_correctly_ignores_old_versions(
    feature: Feature,
    segment_featurestate: FeatureState,
    environment_v2_versioning: Environment,
    admin_client_new: APIClient,
    staff_user: FFAdminUser,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-detail",
        args=[environment_v2_versioning.api_key],
    )

    EnvironmentFeatureVersion.objects.create(
        feature=feature, environment=environment_v2_versioning
    ).publish(staff_user)

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.json()["total_segment_overrides"] == 1
