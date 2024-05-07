import json
import uuid
from datetime import date, datetime, timedelta
from unittest import mock

import pytest
import pytz
from app_analytics.dataclasses import FeatureEvaluationData
from core.constants import FLAGSMITH_UPDATED_AT_HEADER
from django.forms import model_to_dict
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import SettingsWrapper
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from audit.constants import (
    FEATURE_DELETED_MESSAGE,
    IDENTITY_FEATURE_STATE_DELETED_MESSAGE,
    IDENTITY_FEATURE_STATE_UPDATED_MESSAGE,
)
from audit.models import AuditLog, RelatedObjectType
from environments.identities.models import Identity
from environments.models import Environment, EnvironmentAPIKey
from environments.permissions.constants import (
    MANAGE_SEGMENT_OVERRIDES,
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)
from environments.permissions.models import UserEnvironmentPermission
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.value_types import BOOLEAN, INTEGER, STRING
from features.versioning.models import EnvironmentFeatureVersion
from metadata.models import MetadataModelField
from organisations.models import Organisation, OrganisationRole
from projects.models import Project, UserProjectPermission
from projects.permissions import CREATE_FEATURE, VIEW_PROJECT
from projects.tags.models import Tag
from segments.models import Segment
from tests.types import (
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser, UserPermissionGroup
from webhooks.webhooks import WebhookEventType

# patch this function as it's triggering extra threads and causing errors
mock.patch("features.signals.trigger_feature_state_change_webhooks").start()

now = timezone.now()
two_hours_ago = now - timedelta(hours=2)
one_hour_ago = now - timedelta(hours=1)


def test_project_owners_is_read_only_for_feature_create(
    project: Project,
    admin_client_original: APIClient,
    admin_user: FFAdminUser,
) -> None:
    # Given
    default_value = "This is a value"
    data = {
        "name": "test feature",
        "initial_value": default_value,
        "project": project.id,
        "owners": [
            {
                "id": 2,
                "email": "fake_user@mail.com",
                "first_name": "fake",
                "last_name": "user",
            }
        ],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_original.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["owners"]) == 1
    assert response.json()["owners"][0]["id"] == admin_user.id
    assert response.json()["owners"][0]["email"] == admin_user.email


@mock.patch("features.views.trigger_feature_state_change_webhooks")
def test_feature_state_webhook_triggered_when_feature_deleted(
    mocked_trigger_fs_change_webhook: mock.MagicMock,
    project: Project,
    feature: Feature,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_states = list(feature.feature_states.all())
    url = reverse(
        "api-v1:projects:project-features-detail", args=[project.id, feature.id]
    )

    # When
    admin_client_new.delete(url)

    # Then
    mock_calls = [mock.call(fs, WebhookEventType.FLAG_DELETED) for fs in feature_states]
    mocked_trigger_fs_change_webhook.assert_has_calls(mock_calls)


def test_remove_owners_only_remove_specified_owners(
    feature: Feature,
    project: Project,
    admin_client_new: APIClient,
) -> None:
    # Given
    user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
    user_3 = FFAdminUser.objects.create_user(email="user3@mail.com")
    feature.owners.add(user_2, user_3)

    url = reverse(
        "api-v1:projects:project-features-remove-owners",
        args=[project.id, feature.id],
    )
    data = {"user_ids": [user_2.id]}

    # When
    json_response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()
    assert len(json_response["owners"]) == 1
    assert json_response["owners"][0] == {
        "id": user_3.id,
        "email": user_3.email,
        "first_name": user_3.first_name,
        "last_name": user_3.last_name,
        "last_login": None,
    }


def test_audit_log_created_when_feature_state_created_for_identity(
    feature: Feature,
    project: Project,
    identity: Identity,
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:identity-featurestates-list",
        args=[environment.api_key, identity.id],
    )
    data = {"feature": feature.id, "enabled": True}

    # When
    admin_client_new.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE_STATE.name
        ).count()
        == 1
    )

    expected_log_message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (
        feature.name,
        identity.identifier,
    )
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.FEATURE_STATE.name
    )
    assert audit_log.log == expected_log_message


def test_audit_log_created_when_feature_state_updated_for_identity(
    feature: Feature,
    project: Project,
    environment: Environment,
    identity: Identity,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        identity=identity,
        enabled=True,
    )
    url = reverse(
        "api-v1:environments:identity-featurestates-detail",
        args=[environment.api_key, identity.id, feature_state.id],
    )
    data = {"feature": feature.id, "enabled": False}

    # When
    admin_client_new.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE_STATE.name
        ).count()
        == 1
    )

    expected_log_message = IDENTITY_FEATURE_STATE_UPDATED_MESSAGE % (
        feature.name,
        identity.identifier,
    )
    audit_log = AuditLog.objects.get(
        related_object_type=RelatedObjectType.FEATURE_STATE.name
    )
    assert audit_log.log == expected_log_message


def test_audit_log_created_when_feature_state_deleted_for_identity(
    feature: Feature,
    project: Project,
    environment: Environment,
    identity: Identity,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_state = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        identity=identity,
        enabled=True,
    )
    url = reverse(
        "api-v1:environments:identity-featurestates-detail",
        args=[environment.api_key, identity.id, feature_state.id],
    )

    # When
    admin_client_new.delete(url)

    # Then
    assert (
        AuditLog.objects.filter(
            log=IDENTITY_FEATURE_STATE_DELETED_MESSAGE
            % (
                feature.name,
                identity.identifier,
            )
        ).count()
        == 1
    )


def test_when_add_tags_from_different_project_on_feature_create_then_failed(
    project: Project,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    project2 = Project.objects.create(name="Test project2", organisation=organisation)
    tag_other_project = Tag.objects.create(
        label="Wrong Tag",
        color="#fffff",
        description="Test Tag description",
        project=project2,
    )
    feature_name = "test feature"
    data = {
        "name": feature_name,
        "project": project.id,
        "initial_value": "test",
        "tags": [tag_other_project.id],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Check that no features were created successfully.
    assert Feature.objects.filter(name=feature_name, project=project.id).count() == 0


def test_when_add_tags_on_feature_update_then_success(
    project: Project,
    feature: Feature,
    tag_one: Tag,
    admin_client_new: APIClient,
) -> None:
    # Given
    data = {
        "name": feature.name,
        "project": project.id,
        "tags": [tag_one.id],
    }

    url = reverse(
        "api-v1:projects:project-features-detail", args=[project.id, feature.id]
    )

    # When
    response = admin_client_new.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    # check feature was created successfully
    check_feature = Feature.objects.filter(
        name=feature.name, project=project.id
    ).first()

    # check tags added
    assert check_feature.tags.count() == 1


def test_when_add_tags_from_different_project_on_feature_update_then_failed(
    feature: Feature,
    project: Project,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    project2 = Project.objects.create(name="Test project2", organisation=organisation)
    tag_other_project = Tag.objects.create(
        label="Wrong Tag",
        color="#fffff",
        description="Test Tag description",
        project=project2,
    )

    data = {
        "name": feature.name,
        "project": project.id,
        "tags": [tag_other_project.id],
    }
    url = reverse(
        "api-v1:projects:project-features-detail", args=[project.id, feature.id]
    )

    # When
    response = admin_client_new.put(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # check feature was created successfully
    check_feature = Feature.objects.filter(
        name=feature.name, project=project.id
    ).first()

    # check tags not added
    assert check_feature.tags.count() == 0


def test_list_features_is_archived_filter(
    feature: Feature,
    project: Project,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    archived_feature = Feature.objects.create(
        name="archived_feature", project=project, is_archived=True
    )
    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # First test the filter set to true.
    url = f"{base_url}?is_archived=true"

    # When
    response = admin_client_new.get(url)

    # Then
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == archived_feature.id

    # Finally test the filter set to false.
    url = f"{base_url}?is_archived=false"
    response = admin_client_new.get(url)
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == feature.id


def test_put_feature_does_not_update_feature_states(
    feature: Feature,
    project: Project,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    feature.default_enabled = False
    feature.save()

    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    data = model_to_dict(feature)
    data["default_enabled"] = True

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert all(fs.enabled is False for fs in feature.feature_states.all())


@mock.patch("features.views.get_multiple_event_list_for_feature")
def test_get_project_features_influx_data(
    mock_get_event_list: mock.MagicMock,
    feature: Feature,
    project: Project,
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:projects:project-features-get-influx-data",
        args=[project.id, feature.id],
    )
    url = f"{base_url}?environment_id={environment.id}"

    mock_get_event_list.return_value = [
        {
            feature.name: 1,
            "datetime": datetime(2021, 2, 26, 12, 0, 0, tzinfo=pytz.UTC),
        }
    ]

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    mock_get_event_list.assert_called_once_with(
        feature_name=feature.name,
        environment_id=str(environment.id),  # provided as a GET param
        period="24h",  # this is the default but can be provided as a GET param
        aggregate_every="24h",  # this is the default but can be provided as a GET param
    )


def test_regular_user_cannot_create_mv_options_when_creating_feature(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT, CREATE_FEATURE])
    data = {
        "name": "test_feature",
        "default_enabled": True,
        "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    detail = "User must be project admin to modify / create MV options."
    assert response.json()["detail"] == detail


def test_regular_user_cannot_create_mv_options_when_updating_feature(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT, CREATE_FEATURE])

    feature.default_enabled = True
    feature.save()

    data = {
        "name": feature.name,
        "default_enabled": feature.default_enabled,
        "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
    detail = "User must be project admin to modify / create MV options."
    assert response.json()["detail"] == detail


def test_regular_user_can_update_feature_description(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT, CREATE_FEATURE])
    feature.default_enabled = True
    feature.save()
    new_description = "a new description"
    data = {
        "name": feature.name,
        "default_enabled": feature.default_enabled,
        "description": new_description,
    }

    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )

    # When
    response = staff_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    feature.refresh_from_db()
    assert feature.description == new_description


@mock.patch("environments.models.environment_wrapper")
def test_create_feature_only_triggers_write_to_dynamodb_once_per_environment(
    mock_dynamo_environment_wrapper: mock.MagicMock,
    project: Project,
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": "Test feature flag", "type": "FLAG", "project": project.id}

    mock_dynamo_environment_wrapper.is_enabled = True
    mock_dynamo_environment_wrapper.reset_mock()

    # When
    admin_client_new.post(url, data=data)

    # Then
    mock_dynamo_environment_wrapper.write_environments.assert_called_once()


def test_get_flags_for_environment_response(
    api_client: APIClient,
    environment: Environment,
    project: Project,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:flags")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    environment_fs_value = "environment"
    feature = Feature.objects.create(
        name="Test feature",
        project=project,
        initial_value=environment_fs_value,
    )

    segment = Segment.objects.create(name="Test segment", project=project)
    feature_segment = FeatureSegment.objects.create(
        segment=segment,
        feature=feature,
        environment=environment,
    )

    FeatureState.objects.create(
        feature=feature,
        feature_segment=feature_segment,
        environment=environment,
    )
    FeatureState.objects.create(
        identity=identity, environment=environment, feature=feature
    )

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # We only get a single flag back and that is the environment default
    response_json = response.json()
    assert len(response_json) == 1
    assert response_json[0]["feature"]["id"] == feature.id
    assert response_json[0]["feature_state_value"] == environment_fs_value

    # Check that headers set the refreshed last_updated_at.
    environment.refresh_from_db()
    assert response.headers[FLAGSMITH_UPDATED_AT_HEADER] == str(
        environment.updated_at.timestamp()
    )


@pytest.mark.parametrize(
    "environment_value, project_value, disabled_flag_returned",
    (
        (True, True, False),
        (True, False, False),
        (False, True, True),
        (False, False, True),
        (None, True, False),
        (None, False, True),
    ),
)
def test_get_flags_hide_disabled_flags(
    environment_value: bool | None,
    project_value: bool,
    disabled_flag_returned: bool,
    project: Project,
    environment: Environment,
    api_client: APIClient,
) -> None:
    # Given
    project.hide_disabled_flags = project_value
    project.save()

    environment.hide_disabled_flags = environment_value
    environment.save()

    Feature.objects.create(name="disabled_flag", project=project, default_enabled=False)
    Feature.objects.create(name="enabled_flag", project=project, default_enabled=True)

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == (2 if disabled_flag_returned else 1)


def test_get_flags_hide_sensitive_data(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    environment.hide_sensitive_data = True
    environment.save()

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)
    feature_sensitive_fields = [
        "created_date",
        "description",
        "initial_value",
        "default_enabled",
    ]
    fs_sensitive_fields = ["id", "environment", "identity", "feature_segment"]

    # Then
    assert response.status_code == status.HTTP_200_OK
    # Check that the sensitive fields are None
    for flag in response.json():
        for field in fs_sensitive_fields:
            assert flag[field] is None

        for field in feature_sensitive_fields:
            assert flag["feature"][field] is None


def test_get_flags__server_key_only_feature__return_expected(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    feature.is_server_key_only = True
    feature.save()

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not response.json()


def test_get_flags__server_key_only_feature__server_key_auth__return_expected(
    api_client: APIClient,
    environment_api_key: EnvironmentAPIKey,
    feature: Feature,
) -> None:
    # Given
    feature.is_server_key_only = True
    feature.save()

    url = reverse("api-v1:flags")

    # When
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment_api_key.key)
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()


def test_get_feature_states_by_uuid(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    feature_state: FeatureState,
) -> None:
    # Given
    url = reverse(
        "api-v1:features:get-feature-state-by-uuid", args=[feature_state.uuid]
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["uuid"] == str(feature_state.uuid)


def test_deleted_features_are_not_listed(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    feature.delete()

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


def test_get_feature_evaluation_data(
    project: Project,
    feature: Feature,
    environment: Environment,
    mocker: MockerFixture,
    admin_client_new: APIClient,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:projects:project-features-get-evaluation-data",
        args=[project.id, feature.id],
    )
    url = f"{base_url}?environment_id={environment.id}"
    mocked_get_feature_evaluation_data = mocker.patch(
        "features.views.get_feature_evaluation_data", autospec=True
    )
    mocked_get_feature_evaluation_data.return_value = [
        FeatureEvaluationData(count=10, day=date.today()),
        FeatureEvaluationData(count=10, day=date.today() - timedelta(days=1)),
    ]
    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    assert response.json()[0] == {"day": str(date.today()), "count": 10}
    assert response.json()[1] == {
        "day": str(date.today() - timedelta(days=1)),
        "count": 10,
    }
    mocked_get_feature_evaluation_data.assert_called_with(
        feature=feature, period=30, environment_id=environment.id
    )


def test_create_segment_override_forbidden(
    feature: Feature,
    segment: Segment,
    environment: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    # When
    enabled = True
    string_value = "foo"
    data = {
        "feature_state_value": {"string_value": string_value},
        "enabled": enabled,
        "feature_segment": {"segment": segment.id},
    }

    # Staff client lacks permission to create segment.
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 403
    assert response.data == {
        "detail": "You do not have permission to perform this action."
    }


def test_create_segment_override_staff(
    feature: Feature,
    segment: Segment,
    environment: Environment,
    staff_user: FFAdminUser,
    staff_client: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    # When
    enabled = True
    string_value = "foo"
    data = {
        "feature_state_value": {"string_value": string_value},
        "enabled": enabled,
        "feature_segment": {"segment": segment.id},
    }
    user_environment_permission = UserEnvironmentPermission.objects.create(
        user=staff_user, admin=False, environment=environment
    )
    user_environment_permission.permissions.add(MANAGE_SEGMENT_OVERRIDES)

    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == 201
    assert response.data["feature_segment"]["segment"] == segment.id


def test_create_segment_override(
    admin_client_new: APIClient,
    feature: Feature,
    segment: Segment,
    environment: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    enabled = True
    string_value = "foo"
    data = {
        "feature_state_value": {"string_value": string_value},
        "enabled": enabled,
        "feature_segment": {"segment": segment.id},
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    created_override = FeatureState.objects.filter(
        feature=feature, environment=environment, feature_segment__segment=segment
    ).first()
    assert created_override is not None
    assert created_override.enabled is enabled
    assert created_override.get_feature_state_value() == string_value


def test_get_flags_is_not_throttled_by_user_throttle(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
    settings: SettingsWrapper,
):
    # Given
    settings.REST_FRAMEWORK = {"DEFAULT_THROTTLE_RATES": {"user": "1/minute"}}
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    url = reverse("api-v1:flags")

    # When
    for _ in range(10):
        response = api_client.get(url)

        # Then
        assert response.status_code == status.HTTP_200_OK


def test_list_feature_states_from_simple_view_set(
    environment: Environment,
    feature: Feature,
    admin_user: FFAdminUser,
    admin_client_new: APIClient,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    base_url = reverse("api-v1:features:featurestates-list")
    url = f"{base_url}?environment={environment.id}"

    # add another feature
    feature2 = Feature.objects.create(
        name="another_feature", project=environment.project
    )

    # and a new version for the same feature to check for N+1 issues
    v1_feature_state = FeatureState.objects.get(
        environment=environment, feature=feature2
    )
    v1_feature_state.clone(env=environment, version=2, live_from=timezone.now())

    # add another organisation with a project, environment and feature (which should be
    # excluded)
    another_organisation = Organisation.objects.create(name="another_organisation")
    admin_user.add_organisation(another_organisation)
    another_project = Project.objects.create(
        name="another_project", organisation=another_organisation
    )
    Environment.objects.create(name="another_environment", project=another_project)
    Feature.objects.create(project=another_project, name="another_projects_feature")
    UserProjectPermission.objects.create(
        user=admin_user, project=another_project, admin=True
    )

    # add another feature with multivariate options
    mv_feature = Feature.objects.create(
        name="mv_feature", project=environment.project, type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type="unicode",
        string_value="foo",
    )

    # When
    with django_assert_num_queries(9):
        response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


def test_list_feature_states_nested_environment_view_set(
    environment: Environment,
    project: Project,
    feature: Feature,
    admin_client_new: APIClient,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # Add an MV feature
    mv_feature = Feature.objects.create(
        name="mv_feature", project=project, type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type="unicode",
        string_value="foo",
    )

    # Add another feature
    second_feature = Feature.objects.create(name="another_feature", project=project)

    # create some new versions to test N+1 issues
    v1_feature_state = FeatureState.objects.get(
        feature=second_feature, environment=environment
    )
    v2_feature_state = v1_feature_state.clone(
        env=environment, version=2, live_from=timezone.now()
    )
    v2_feature_state.clone(env=environment, version=3, live_from=timezone.now())

    # When
    with django_assert_num_queries(8):
        response = admin_client_new.get(base_url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


def test_environment_feature_states_filter_using_feature_name(
    environment: Environment,
    project: Project,
    feature: Feature,
    admin_client_new: APIClient,
) -> None:
    # Given
    Feature.objects.create(name="another_feature", project=project)
    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    url = f"{base_url}?feature_name={feature.name}"

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["feature"] == feature.id


def test_environment_feature_states_filter_to_show_identity_override_only(
    environment: Environment,
    feature: Feature,
    admin_client_new: APIClient,
) -> None:
    # Given
    FeatureState.objects.get(environment=environment, feature=feature)

    identifier = "test-identity"
    identity = Identity.objects.create(identifier=identifier, environment=environment)
    FeatureState.objects.create(
        environment=environment, feature=feature, identity=identity
    )

    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    url = base_url + "?anyIdentity&feature=" + str(feature.id)

    # When
    res = admin_client_new.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK
    assert len(res.json().get("results")) == 1
    assert res.json()["results"][0]["identity"]["identifier"] == identifier


def test_environment_feature_states_only_returns_latest_versions(
    environment: Environment,
    feature: Feature,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)
    feature_state_v2 = feature_state.clone(
        env=environment, live_from=timezone.now(), version=2
    )

    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == feature_state_v2.id


def test_environment_feature_states_does_not_return_null_versions(
    environment: Environment,
    feature: Feature,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    FeatureState.objects.create(environment=environment, feature=feature, version=None)

    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == feature_state.id

    # Feature tests


def test_create_feature_default_is_archived_is_false(
    admin_client_new: APIClient, project: Project
) -> None:
    # Given
    data = {
        "name": "test feature",
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert response["is_archived"] is False


def test_update_feature_is_archived(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    feature = Feature.objects.create(name="test feature", project=project)
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    data = {"name": "test feature", "is_archived": True}

    # When
    response = admin_client_new.put(url, data=data).json()

    # Then
    assert response["is_archived"] is True


def test_should_create_feature_states_when_feature_created(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
) -> None:
    # Given - set up data
    environment_2 = Environment.objects.create(
        name="Test environment 2", project=project
    )
    default_value = "This is a value"
    data = {
        "name": "test feature",
        "initial_value": default_value,
        "project": project.id,
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    # check feature was created successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 1

    # check feature was added to environment
    assert FeatureState.objects.filter(environment=environment).count() == 1
    assert FeatureState.objects.filter(environment=environment_2).count() == 1

    # check that value was correctly added to feature state
    feature_state = FeatureState.objects.filter(environment=environment).first()
    assert feature_state.get_feature_state_value() == default_value


@pytest.mark.parametrize("default_value", [(12), (True), ("test")])
def test_should_create_feature_states_with_value_when_feature_created(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    default_value: int | bool | str,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {
        "name": "test feature",
        "initial_value": default_value,
        "project": project.id,
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    # check feature was created successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 1

    # check feature was added to environment
    assert FeatureState.objects.filter(environment=environment).count() == 1

    # check that value was correctly added to feature state
    feature_state = FeatureState.objects.filter(environment=environment).first()
    assert feature_state.get_feature_state_value() == default_value


def test_should_delete_feature_states_when_feature_deleted(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check feature was deleted successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 0

    # check feature was removed from all environments
    assert (
        FeatureState.objects.filter(environment=environment, feature=feature).count()
        == 0
    )
    assert (
        FeatureState.objects.filter(environment=environment, feature=feature).count()
        == 0
    )


def test_create_feature_returns_201_if_name_matches_regex(
    admin_client_new: APIClient, project: Project
) -> None:
    # Given
    project.feature_name_regex = "^[a-z_]{18}$"
    project.save()

    # feature name that has 18 characters
    feature_name = "valid_feature_name"

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": feature_name, "type": "FLAG", "project": project.id}

    # When
    response = admin_client_new.post(url, data=data)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_feature_returns_400_if_name_does_not_matches_regex(
    admin_client_new: APIClient, project: Project
) -> None:
    # Given
    project.feature_name_regex = "^[a-z]{18}$"
    project.save()

    # feature name longer than 18 characters
    feature_name = "not_a_valid_feature_name"

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": feature_name, "type": "FLAG", "project": project.id}

    # When
    response = admin_client_new.post(url, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["name"][0]
        == f"Feature name must match regex: {project.feature_name_regex}"
    )


def test_audit_log_created_when_feature_created(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": "Test feature flag", "type": "FLAG", "project": project.id}

    # When
    response = admin_client_new.post(url, data=data)
    feature_id = response.json()["id"]

    # Then
    # Audit log exists for the feature
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name,
            related_object_id=feature_id,
        ).count()
        == 1
    )
    # and Audit log exists for every environment
    assert AuditLog.objects.filter(
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        project=project,
        environment__in=project.environments.all(),
    ).count() == len(project.environments.all())


def test_audit_log_created_when_feature_updated(
    admin_client_new: APIClient, project: Project, feature: Feature
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    data = {
        "name": "Test Feature updated",
        "type": "FLAG",
        "project": project.id,
    }

    # When
    admin_client_new.put(url, data=data)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name
        ).count()
        == 1
    )


def test_audit_logs_created_when_feature_deleted(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    feature_states_ids = list(feature.feature_states.values_list("id", flat=True))

    # When
    admin_client_new.delete(url)

    # Then
    # Audit log exists for the feature
    assert AuditLog.objects.get(
        related_object_type=RelatedObjectType.FEATURE.name,
        related_object_id=feature.id,
        log=FEATURE_DELETED_MESSAGE % feature.name,
    )
    # and audit logs exists for all feature states for that feature
    assert AuditLog.objects.filter(
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        related_object_id__in=feature_states_ids,
        log=FEATURE_DELETED_MESSAGE % feature.name,
    ).count() == len(feature_states_ids)


def test_should_create_tags_when_feature_created(
    admin_client_new: APIClient,
    project: Project,
    tag_one: Tag,
    tag_two: Tag,
) -> None:
    # Given - set up data
    default_value = "Test"
    feature_name = "Test feature"
    data = {
        "name": feature_name,
        "project": project.id,
        "initial_value": default_value,
        "tags": [tag_one.id, tag_two.id],
    }

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    # check feature was created successfully
    feature = Feature.objects.filter(name=feature_name, project=project.id).first()

    # check feature is tagged
    assert feature.tags.count() == 2
    assert list(feature.tags.all()) == [tag_one, tag_two]


def test_add_owners_fails_if_user_not_found(
    admin_client_new: APIClient, project: Project
) -> None:
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)

    # Users have no association to the project or organisation.
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
    url = reverse(
        "api-v1:projects:project-features-add-owners",
        args=[project.id, feature.id],
    )
    data = {"user_ids": [user_1.id, user_2.id]}

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == ["Some users not found"]
    assert feature.owners.filter(id__in=[user_1.id, user_2.id]).count() == 0


def test_add_owners_adds_owner(
    staff_user: FFAdminUser,
    admin_user: FFAdminUser,
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    UserProjectPermission.objects.create(
        user=staff_user, project=project
    ).add_permission(VIEW_PROJECT)

    url = reverse(
        "api-v1:projects:project-features-add-owners",
        args=[project.id, feature.id],
    )
    data = {"user_ids": [staff_user.id, admin_user.id]}

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    json_response = response.json()
    # Then
    assert len(json_response["owners"]) == 2
    assert json_response["owners"][0] == {
        "id": staff_user.id,
        "email": staff_user.email,
        "first_name": staff_user.first_name,
        "last_name": staff_user.last_name,
        "last_login": None,
    }
    assert json_response["owners"][1] == {
        "id": admin_user.id,
        "email": admin_user.email,
        "first_name": admin_user.first_name,
        "last_name": admin_user.last_name,
        "last_login": None,
    }


def test_add_group_owners_adds_group_owner(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Second Group", organisation=organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)
    group_2.users.add(user_1)

    url = reverse(
        "api-v1:projects:project-features-add-group-owners",
        args=[project.id, feature.id],
    )

    data = {"group_ids": [group_1.id, group_2.id]}

    # When
    json_response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["group_owners"]) == 2
    assert json_response["group_owners"][0] == {
        "id": group_1.id,
        "name": group_1.name,
    }
    assert json_response["group_owners"][1] == {
        "id": group_2.id,
        "name": group_2.name,
    }


def test_remove_group_owners_removes_group_owner(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="To be removed group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="To be kept group", organisation=organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)
    group_2.users.add(user_1)

    feature.group_owners.add(group_1.id, group_2.id)

    url = reverse(
        "api-v1:projects:project-features-remove-group-owners",
        args=[project.id, feature.id],
    )

    # Note that only group_1 is set to be removed.
    data = {"group_ids": [group_1.id]}

    # When
    json_response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["group_owners"]) == 1
    assert json_response["group_owners"][0] == {
        "id": group_2.id,
        "name": group_2.name,
    }


def test_remove_group_owners_when_nonexistent(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="To be removed group", organisation=organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)

    assert feature.group_owners.count() == 0

    url = reverse(
        "api-v1:projects:project-features-remove-group-owners",
        args=[project.id, feature.id],
    )

    # Note that group_1 is not present, but it should work
    # anyway since there may have been a double request or two
    # users working at the same time.
    data = {"group_ids": [group_1.id]}

    # When
    json_response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["group_owners"]) == 0


def test_add_group_owners_with_wrong_org_group(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
    organisation = project.organisation
    other_organisation = Organisation.objects.create(name="Orgy")

    group_1 = UserPermissionGroup.objects.create(
        name="Valid Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Invalid Group", organisation=other_organisation
    )
    user_1.add_organisation(organisation, OrganisationRole.ADMIN)
    user_2.add_organisation(other_organisation, OrganisationRole.ADMIN)
    group_1.users.add(user_1)
    group_2.users.add(user_2)

    url = reverse(
        "api-v1:projects:project-features-add-group-owners",
        args=[project.id, feature.id],
    )

    data = {"group_ids": [group_1.id, group_2.id]}

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == 400
    response.json() == {"non_field_errors": ["Some groups not found"]}


def test_list_features_return_tags(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    Feature.objects.create(name="test_feature", project=project)
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    feature = response_json["results"][0]
    assert "tags" in feature


def test_list_features_group_owners(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    feature = Feature.objects.create(name="test_feature", project=project)
    organisation = project.organisation
    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Second Group", organisation=organisation
    )
    feature.group_owners.add(group_1.id, group_2.id)

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    feature = response_json["results"][1]
    assert feature["group_owners"][0] == {
        "id": group_1.id,
        "name": group_1.name,
    }
    assert feature["group_owners"][1] == {
        "id": group_2.id,
        "name": group_2.name,
    }


def test_project_admin_can_create_mv_options_when_creating_feature(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    data = {
        "name": "test_feature",
        "default_enabled": True,
        "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert len(response_json["multivariate_options"]) == 1


def test_get_feature_by_uuid(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:features:get-feature-by-uuid", args=[feature.uuid])

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == feature.id
    assert response.json()["uuid"] == str(feature.uuid)


def test_get_feature_by_uuid_returns_404_if_feature_does_not_exists(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:features:get-feature-by-uuid", args=[uuid.uuid4()])

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_feature_state_value_triggers_dynamo_rebuild(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    feature: Feature,
    feature_state: FeatureState,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    project.enable_dynamo_db = True
    project.save()

    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )
    mock_dynamo_environment_wrapper = mocker.patch(
        "environments.models.environment_wrapper"
    )

    # When
    response = admin_client_new.patch(
        url,
        data=json.dumps({"feature_state_value": "new value"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    mock_dynamo_environment_wrapper.write_environments.assert_called_once()


def test_create_segment_overrides_creates_correct_audit_log_messages(
    admin_client_new: APIClient,
    feature: Feature,
    segment: Segment,
    environment: Environment,
) -> None:
    # Given
    another_segment = Segment.objects.create(
        name="Another segment", project=segment.project
    )

    feature_segments_url = reverse("api-v1:features:feature-segment-list")
    feature_states_url = reverse("api-v1:features:featurestates-list")

    # When
    # we create 2 segment overrides for the feature
    for _segment in (segment, another_segment):
        feature_segment_response = admin_client_new.post(
            feature_segments_url,
            data={
                "feature": feature.id,
                "segment": _segment.id,
                "environment": environment.id,
            },
        )
        assert feature_segment_response.status_code == status.HTTP_201_CREATED
        feature_segment_id = feature_segment_response.json()["id"]
        feature_state_response = admin_client_new.post(
            feature_states_url,
            data={
                "feature": feature.id,
                "feature_segment": feature_segment_id,
                "environment": environment.id,
                "enabled": True,
            },
        )
        assert feature_state_response.status_code == status.HTTP_201_CREATED

    # Then
    assert AuditLog.objects.count() == 2
    assert (
        AuditLog.objects.filter(
            log=f"Flag state / Remote config value updated for feature "
            f"'{feature.name}' and segment '{segment.name}'"
        ).count()
        == 1
    )
    assert (
        AuditLog.objects.filter(
            log=f"Flag state / Remote config value updated for feature "
            f"'{feature.name}' and segment '{another_segment.name}'"
        ).count()
        == 1
    )


def test_list_features_provides_information_on_number_of_overrides(
    feature: Feature,
    segment: Segment,
    segment_featurestate: FeatureState,
    identity: Identity,
    identity_featurestate: FeatureState,
    project: Project,
    environment: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    url = "%s?environment=%d" % (
        reverse("api-v1:projects:project-features-list", args=[project.id]),
        environment.id,
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["num_segment_overrides"] == 1
    assert response_json["results"][0]["num_identity_overrides"] == 1


def test_list_features_provides_correct_information_on_number_of_overrides_based_on_version(
    feature: Feature,
    segment: Segment,
    project: Project,
    environment_v2_versioning: Environment,
    admin_client_new: APIClient,
    admin_user: FFAdminUser,
):
    # Given
    url = "%s?environment=%d" % (
        reverse("api-v1:projects:project-features-list", args=[project.id]),
        environment_v2_versioning.id,
    )

    # let's create a new version with a segment override
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.create(
        feature=feature,
        environment=environment_v2_versioning,
        feature_segment=FeatureSegment.objects.create(
            feature=feature,
            environment=environment_v2_versioning,
            segment=segment,
        ),
        environment_feature_version=version_2,
    )
    version_2.publish(admin_user)

    # and now let's create a new version which removes the segment override
    version_3 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    FeatureState.objects.filter(
        environment_feature_version=version_3,
        feature_segment__segment=segment,
    ).delete()
    version_3.publish(admin_user)

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1

    # The number of segment overrides in the latest version should be 0
    assert response_json["results"][0]["num_segment_overrides"] == 0


def test_list_features_provides_segment_overrides_for_dynamo_enabled_project(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature = Feature.objects.create(
        name="test_feature", project=dynamo_enabled_project
    )
    segment = Segment.objects.create(
        name="test_segment", project=dynamo_enabled_project
    )
    feature_segment = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=dynamo_enabled_project_environment_one,
    )
    FeatureState.objects.create(
        feature=feature,
        environment=dynamo_enabled_project_environment_one,
        feature_segment=feature_segment,
    )
    url = "%s?environment=%d" % (
        reverse(
            "api-v1:projects:project-features-list", args=[dynamo_enabled_project.id]
        ),
        dynamo_enabled_project_environment_one.id,
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["num_segment_overrides"] == 1
    assert response_json["results"][0]["num_identity_overrides"] is None


def test_create_segment_override_reaching_max_limit(
    admin_client_new: APIClient,
    feature: Feature,
    segment: Segment,
    project: Project,
    environment: Environment,
    settings: SettingsWrapper,
) -> None:
    # Given
    project.max_segment_overrides_allowed = 1
    project.save()

    url = reverse(
        "api-v1:environments:create-segment-override",
        args=[environment.api_key, feature.id],
    )

    data = {
        "feature_state_value": {"string_value": "value"},
        "enabled": True,
        "feature_segment": {"segment": segment.id},
    }

    # Now, crate the first override
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Then
    # Try to create another override
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["environment"]
        == "The environment has reached the maximum allowed segments overrides limit."
    )
    assert environment.feature_segments.count() == 1


def test_create_feature_reaching_max_limit(
    admin_client_new: APIClient,
    project: Project,
    settings: SettingsWrapper,
) -> None:
    # Given
    project.max_features_allowed = 1
    project.save()

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Now, crate the first feature
    response = admin_client_new.post(
        url, data={"name": "test_feature", "project": project.id}
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Then
    # Try to create another feature
    response = admin_client_new.post(
        url, data={"name": "second_feature", "project": project.id}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["project"]
        == "The Project has reached the maximum allowed features limit."
    )


def test_create_segment_override_using_environment_viewset(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment.id,
        "identity": None,
        "feature_segment": feature_segment.id,
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response.json()["feature_state_value"] == new_value


def test_cannot_create_feature_state_for_feature_from_different_project(
    admin_client_new: APIClient,
    environment: Environment,
    project_two_feature: Feature,
    feature_segment: FeatureSegment,
    project_two: Project,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": project_two_feature.id,
        "environment": environment.id,
        "identity": None,
        "feature_segment": feature_segment.id,
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["feature"][0] == "Feature does not exist in project"


def test_create_feature_state_environment_is_read_only(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    feature_segment: FeatureSegment,
    environment_two: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment_two.id,
        "feature_segment": feature_segment.id,
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["environment"] == environment.id


def test_cannot_create_feature_state_of_feature_from_different_project(
    admin_client_new: APIClient,
    environment: Environment,
    project_two_feature: Feature,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": project_two_feature.id,
        "environment": environment.id,
        "identity": None,
        "feature_segment": feature_segment.id,
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["feature"][0] == "Feature does not exist in project"


def test_create_feature_state_environment_field_is_read_only(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    feature_segment: FeatureSegment,
    environment_two: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    new_value = "new-value"
    data = {
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment_two.id,
        "feature_segment": feature_segment.id,
    }

    # When
    response = admin_client_new.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["environment"] == environment.id


def test_cannot_update_environment_of_a_feature_state(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    feature_state: FeatureState,
    environment_two: Environment,
) -> None:
    # Given
    url = reverse(
        "api-v1:environments:environment-featurestates-detail",
        args=[environment.api_key, feature_state.id],
    )
    new_value = "new-value"
    data = {
        "id": feature_state.id,
        "feature_state_value": new_value,
        "enabled": False,
        "feature": feature.id,
        "environment": environment_two.id,
        "identity": None,
        "feature_segment": None,
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then - it did not change the environment field on the feature state
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["environment"][0]
        == "Cannot change the environment of a feature state"
    )


def test_cannot_update_feature_of_a_feature_state(
    admin_client_new: APIClient,
    environment: Environment,
    feature: Feature,
    feature_state: FeatureState,
    identity: Identity,
    project: Project,
) -> None:
    # Given
    another_feature = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    url = reverse("api-v1:features:featurestates-detail", args=[feature_state.id])

    feature_state_value = "New value"
    data = {
        "enabled": True,
        "feature_state_value": {"type": "unicode", "string_value": feature_state_value},
        "environment": environment.id,
        "feature": another_feature.id,
    }

    # When
    response = admin_client_new.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert another_feature.feature_states.count() == 1
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["feature"][0] == "Cannot change the feature of a feature state"
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_without_required_metadata_returns_400(
    project: Project,
    client: APIClient,
    required_a_feature_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    description = "This is the description"
    data = {
        "name": "Test feature",
        "description": description,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_with_optional_metadata_returns_201(
    project: Project,
    client: APIClient,
    optional_b_feature_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test feature",
        "description": description,
        "metadata": [
            {
                "model_field": optional_b_feature_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == optional_b_feature_metadata_field.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_with_required_metadata_returns_201(
    project: Project,
    client: APIClient,
    required_a_feature_metadata_field: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test feature",
        "description": description,
        "metadata": [
            {
                "model_field": required_a_feature_metadata_field.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == required_a_feature_metadata_field.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_with_required_metadata_using_organisation_content_typereturns_201(
    project: Project,
    client: APIClient,
    required_a_feature_metadata_field_using_organisation_content_type: MetadataModelField,
) -> None:
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    description = "This is the description"
    field_value = 10
    data = {
        "name": "Test feature",
        "description": description,
        "metadata": [
            {
                "model_field": required_a_feature_metadata_field_using_organisation_content_type.id,
                "field_value": field_value,
            },
        ],
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert (
        response.json()["metadata"][0]["model_field"]
        == required_a_feature_metadata_field_using_organisation_content_type.id
    )
    assert response.json()["metadata"][0]["field_value"] == str(field_value)


def test_create_segment_override__using_simple_feature_state_viewset__allows_manage_segment_overrides(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES])

    url = reverse("api-v1:features:featurestates-list")

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    assert FeatureState.objects.filter(
        feature=feature, environment=environment, feature_segment=feature_segment
    ).exists()


def test_create_segment_override__using_simple_feature_state_viewset__denies_update_feature_state(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])

    url = reverse("api-v1:features:featurestates-list")

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_segment_override__using_simple_feature_state_viewset__allows_manage_segment_overrides(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
    segment_featurestate: FeatureState,
) -> None:
    # Given
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES])

    url = reverse(
        "api-v1:features:featurestates-detail", args=[segment_featurestate.id]
    )

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert FeatureState.objects.filter(
        feature=feature,
        environment=environment,
        feature_segment=feature_segment,
        enabled=True,
        feature_state_value__string_value="foo",
    ).exists()


def test_update_segment_override__using_simple_feature_state_viewset__denies_update_feature_state(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment: Environment,
    feature: Feature,
    segment: Segment,
    feature_segment: FeatureSegment,
    segment_featurestate: FeatureState,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])

    url = reverse(
        "api-v1:features:featurestates-detail", args=[segment_featurestate.id]
    )

    data = {
        "feature": feature.id,
        "environment": environment.id,
        "feature_segment": feature_segment.id,
        "enabled": True,
        "feature_state_value": {
            "type": "unicode",
            "string_value": "foo",
        },
    }

    # When
    response = staff_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_features_n_plus_1(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}"

    # add some more versions to test for N+1 issues
    v1_feature_state = FeatureState.objects.get(
        feature=feature, environment=environment
    )
    for i in range(2, 4):
        v1_feature_state.clone(env=environment, version=i, live_from=timezone.now())

    # When
    with django_assert_num_queries(17):
        response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_list_features_with_union_tag(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    tag1 = Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    tag2 = Tag.objects.create(
        label="Test Tag2",
        color="#fffff",
        description="Test Tag2 description",
        project=project,
    )
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature2.tags.add(tag1)
    feature3.tags.add(tag2)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = (
        f"{base_url}?environment={environment.id}&tags={tag1.id}"
        f",{tag2.id}&tag_strategy=UNION"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # The first feature has been filtered out of the results.
    assert len(response.data["results"]) == 2

    assert response.data["results"][0]["id"] == feature2.id
    assert response.data["results"][0]["tags"] == [tag1.id]
    assert response.data["results"][1]["id"] == feature3.id
    assert response.data["results"][1]["tags"] == [tag2.id]


def test_list_features_with_intersection_tag(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    tag1 = Tag.objects.create(
        label="Test Tag",
        color="#fffff",
        description="Test Tag description",
        project=project,
    )
    tag2 = Tag.objects.create(
        label="Test Tag2",
        color="#fffff",
        description="Test Tag2 description",
        project=project,
    )
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature2.tags.add(tag1, tag2)
    feature3.tags.add(tag2)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = (
        f"{base_url}?environment={environment.id}&tags={tag1.id}"
        f",{tag2.id}&tag_strategy=INTERSECTION"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Only feature2 has both tags, so it is the only result.
    assert len(response.data["results"]) == 1

    assert response.data["results"][0]["id"] == feature2.id
    assert response.data["results"][0]["tags"] == [tag1.id, tag2.id]


def test_list_features_with_feature_state(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
    identity: Identity,
    feature_segment: FeatureSegment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="fancy_feature", project=project, initial_value="gone"
    )

    Environment.objects.create(
        name="Out of test scope environment",
        project=project,
    )

    feature_state1 = feature.feature_states.filter(environment=environment).first()
    feature_state1.enabled = True
    feature_state1.version = 1
    feature_state1.save()

    feature_state_value1 = feature_state1.feature_state_value
    feature_state_value1.string_value = None
    feature_state_value1.integer_value = 1945
    feature_state_value1.type = INTEGER
    feature_state_value1.save()

    # This should be ignored due to versioning.
    feature_state_versioned = FeatureState.objects.create(
        feature=feature,
        environment=environment,
        enabled=True,
        version=100,
    )
    feature_state_value_versioned = feature_state_versioned.feature_state_value
    feature_state_value_versioned.string_value = None
    feature_state_value_versioned.integer_value = 2005
    feature_state_value_versioned.type = INTEGER
    feature_state_value_versioned.save()

    feature_state2 = feature2.feature_states.filter(environment=environment).first()
    feature_state2.enabled = True
    feature_state2.save()

    feature_state_value2 = feature_state2.feature_state_value
    feature_state_value2.string_value = None
    feature_state_value2.boolean_value = True
    feature_state_value2.type = BOOLEAN
    feature_state_value2.save()

    feature_state_value3 = (
        feature3.feature_states.filter(environment=environment)
        .first()
        .feature_state_value
    )
    feature_state_value3.string_value = "present"
    feature_state_value3.save()

    # This should be ignored due to identity being set.
    FeatureState.objects.create(
        feature=feature2,
        environment=environment,
        identity=identity,
    )

    # This should be ignored due to feature segment being set.
    FeatureState.objects.create(
        feature=feature2,
        environment=environment,
        feature_segment=feature_segment,
    )

    # Multivariate should be ignored.
    MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=30,
        type=STRING,
        string_value="mv_feature_option1",
    )
    MultivariateFeatureOption.objects.create(
        feature=feature2,
        default_percentage_allocation=70,
        type=STRING,
        string_value="mv_feature_option2",
    )

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}"

    # When
    with django_assert_num_queries(17):
        response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 3
    results = response.data["results"]

    assert results[0]["environment_feature_state"]["enabled"] is True
    assert results[0]["environment_feature_state"]["feature_state_value"] == 2005
    assert results[0]["name"] == feature.name
    assert results[1]["environment_feature_state"]["enabled"] is True
    assert results[1]["environment_feature_state"]["feature_state_value"] is True
    assert results[1]["name"] == feature2.name
    assert results[2]["environment_feature_state"]["enabled"] is False
    assert results[2]["environment_feature_state"]["feature_state_value"] == "present"
    assert results[2]["name"] == feature3.name


def test_list_features_with_filter_by_value_search_string_and_int(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment_v2_versioning: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    environment = environment_v2_versioning

    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature4 = Feature.objects.create(
        name="fancy_feature", project=project, initial_value="fancy"
    )

    Environment.objects.create(
        name="Out of test scope environment",
        project=project,
    )

    environment_feature_version1 = EnvironmentFeatureVersion.objects.create(
        environment=environment,
        feature=feature,
    )

    feature_state1 = FeatureState.objects.filter(
        environment_feature_version=environment_feature_version1
    ).first()
    feature_state1.enabled = True
    feature_state1.save()

    # Create a secondary feature state that will be versioned in the past.
    environment_feature_version1b = EnvironmentFeatureVersion.objects.create(
        environment=environment,
        feature=feature,
    )

    feature_state1b = FeatureState.objects.filter(
        environment_feature_version=environment_feature_version1b
    ).first()
    feature_state1b.enabled = False
    feature_state1b.save()

    environment_feature_version1b.publish(staff_user)

    environment_feature_version1.publish(staff_user)

    feature_state_value1 = feature_state1.feature_state_value
    feature_state_value1.string_value = None
    feature_state_value1.integer_value = 1945
    feature_state_value1.type = INTEGER
    feature_state_value1.save()

    feature_state2 = feature2.feature_states.filter(environment=environment).first()
    feature_state2.enabled = True
    feature_state2.save()

    feature_state_value2 = feature_state2.feature_state_value
    feature_state_value2.string_value = None
    feature_state_value2.boolean_value = True
    feature_state_value2.type = BOOLEAN
    feature_state_value2.save()

    feature_state_value3 = (
        feature3.feature_states.filter(environment=environment)
        .first()
        .feature_state_value
    )
    feature_state_value3.string_value = "present"
    feature_state_value3.type = STRING
    feature_state_value3.save()

    feature_state4 = feature4.feature_states.filter(environment=environment).first()
    feature_state4.enabled = True
    feature_state4.save()

    feature_state_value4 = feature_state4.feature_state_value
    feature_state_value4.string_value = "year 1945"
    feature_state_value4.type = STRING
    feature_state_value4.save()

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}&value_search=1945&is_enabled=true"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    # Only two features met the criteria.
    assert len(response.data["results"]) == 2
    features = {result["name"] for result in response.data["results"]}
    assert feature.name in features
    assert feature4.name in features


def test_list_features_with_filter_by_search_value_boolean(
    staff_client: APIClient,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])
    feature2 = Feature.objects.create(
        name="another_feature", project=project, initial_value="initial_value"
    )
    feature3 = Feature.objects.create(
        name="missing_feature", project=project, initial_value="gone"
    )
    feature4 = Feature.objects.create(
        name="fancy_feature", project=project, initial_value="fancy"
    )

    Environment.objects.create(
        name="Out of test scope environment",
        project=project,
    )

    feature_state1 = feature.feature_states.filter(environment=environment).first()
    feature_state1.enabled = True
    feature_state1.save()

    feature_state_value1 = feature_state1.feature_state_value
    feature_state_value1.string_value = None
    feature_state_value1.integer_value = 1945
    feature_state_value1.type = INTEGER
    feature_state_value1.save()

    feature_state2 = feature2.feature_states.filter(environment=environment).first()
    feature_state2.enabled = False
    feature_state2.save()

    feature_state_value2 = feature_state2.feature_state_value
    feature_state_value2.string_value = None
    feature_state_value2.boolean_value = True
    feature_state_value2.type = BOOLEAN
    feature_state_value2.save()

    feature_state_value3 = (
        feature3.feature_states.filter(environment=environment)
        .first()
        .feature_state_value
    )
    feature_state_value3.string_value = "present"
    feature_state_value3.type = STRING
    feature_state_value3.save()

    feature_state4 = feature4.feature_states.filter(environment=environment).first()
    feature_state4.enabled = True
    feature_state4.save()

    feature_state_value4 = feature_state4.feature_state_value
    feature_state_value4.string_value = "year 1945"
    feature_state_value4.type = STRING
    feature_state_value4.save()

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])
    url = f"{base_url}?environment={environment.id}&value_search=true&is_enabled=false"

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["name"] == feature2.name


def test_simple_feature_state_returns_only_latest_versions(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    environment_v2_versioning: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    # Given
    url = "%s?environment=%d" % (
        reverse("api-v1:features:featurestates-list"),
        environment_v2_versioning.id,
    )

    with_environment_permissions(
        [VIEW_ENVIRONMENT], environment_id=environment_v2_versioning.id
    )

    # Let's create some new versions, with some segment overrides
    version_2 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    feature_segment_v2 = FeatureSegment.objects.create(
        feature=feature,
        segment=segment,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
    )
    FeatureState.objects.create(
        feature_segment=feature_segment_v2,
        feature=feature,
        environment=environment_v2_versioning,
        environment_feature_version=version_2,
    )
    version_2.publish(staff_user)

    version_3 = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )
    version_3.publish(staff_user)

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 2


@pytest.mark.freeze_time(two_hours_ago)
def test_feature_list_last_modified_values(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    environment_v2_versioning: Environment,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    # another v2 versioning environment
    environment_v2_versioning_2 = Environment.objects.create(
        name="environment 2", project=project, use_v2_feature_versioning=True
    )

    url = "{base_url}?environment={environment_id}".format(
        base_url=reverse("api-v1:projects:project-features-list", args=[project.id]),
        environment_id=environment_v2_versioning.id,
    )

    with_project_permissions([VIEW_PROJECT])

    with freeze_time(one_hour_ago):
        # create a new published version in another environment, simulated to be one hour ago
        environment_v2_versioning_2_version_2 = (
            EnvironmentFeatureVersion.objects.create(
                environment=environment_v2_versioning_2, feature=feature
            )
        )
        environment_v2_versioning_2_version_2.publish(staff_user)

    with freeze_time(now):
        # and create a new unpublished version in the current environment, simulated to be now
        # this shouldn't affect the values returned
        EnvironmentFeatureVersion.objects.create(
            environment=environment_v2_versioning, feature=feature
        )

    # let's add a few more features to ensure we aren't adding N+1 issues
    for i in range(2):
        Feature.objects.create(name=f"feature_{i}", project=project)

    # When
    with django_assert_num_queries(19):  # TODO: reduce this number of queries!
        response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3

    feature_data = next(
        filter(lambda r: r["id"] == feature.id, response_json["results"])
    )
    assert feature_data["last_modified_in_any_environment"] == one_hour_ago.isoformat()
    assert (
        feature_data["last_modified_in_current_environment"]
        == two_hours_ago.isoformat()
    )


def test_filter_features_with_owners(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    admin_user: FFAdminUser,
    project: Project,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="included_feature", project=project, initial_value="initial_value"
    )
    Feature.objects.create(
        name="not_included_feature", project=project, initial_value="gone"
    )

    # Include admin only in the first feature.
    feature.owners.add(admin_user)

    # Include staff only in the second feature.
    feature2.owners.add(staff_user)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Search for both users in the owners query param.
    url = (
        f"{base_url}?environment={environment.id}&"
        f"owners={admin_user.id},{staff_user.id}"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == feature.id
    assert response.data["results"][1]["id"] == feature2.id


def test_filter_features_with_group_owners(
    staff_client: APIClient,
    project: Project,
    organisation: Organisation,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="included_feature", project=project, initial_value="initial_value"
    )
    Feature.objects.create(
        name="not_included_feature", project=project, initial_value="gone"
    )

    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )
    group_2 = UserPermissionGroup.objects.create(
        name="Second Group", organisation=organisation
    )

    feature.group_owners.add(group_1)
    feature2.group_owners.add(group_2)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Search for both users in the owners query param.
    url = (
        f"{base_url}?environment={environment.id}&"
        f"group_owners={group_1.id},{group_2.id}"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == feature.id
    assert response.data["results"][1]["id"] == feature2.id


def test_filter_features_with_owners_and_group_owners_together(
    staff_client: APIClient,
    staff_user: FFAdminUser,
    project: Project,
    organisation: Organisation,
    feature: Feature,
    with_project_permissions: WithProjectPermissionsCallable,
    environment: Environment,
) -> None:
    # Given
    with_project_permissions([VIEW_PROJECT])

    feature2 = Feature.objects.create(
        name="included_feature", project=project, initial_value="initial_value"
    )
    Feature.objects.create(
        name="not_included_feature", project=project, initial_value="gone"
    )

    group_1 = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )

    feature.group_owners.add(group_1)
    feature2.owners.add(staff_user)

    base_url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Search for both users in the owners query param.
    url = (
        f"{base_url}?environment={environment.id}&"
        f"group_owners={group_1.id}&owners={staff_user.id}"
    )
    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert len(response.data["results"]) == 2
    assert response.data["results"][0]["id"] == feature.id
    assert response.data["results"][1]["id"] == feature2.id
