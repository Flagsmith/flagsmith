import json
import uuid

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from audit.constants import FEATURE_DELETED_MESSAGE
from audit.models import AuditLog, RelatedObjectType
from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from organisations.models import Organisation
from projects.models import Project, UserProjectPermission
from projects.permissions import VIEW_PROJECT
from segments.models import Segment
from users.models import FFAdminUser


def test_list_feature_states_from_simple_view_set(
    environment, feature, admin_user, admin_client, django_assert_num_queries
):
    # Given
    base_url = reverse("api-v1:features:featurestates-list")
    url = f"{base_url}?environment={environment.id}"

    # add another feature
    Feature.objects.create(name="another_feature", project=environment.project)

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
    with django_assert_num_queries(8):
        response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


def test_list_feature_states_nested_environment_view_set(
    environment, project, feature, admin_client, django_assert_num_queries
):
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
    Feature.objects.create(name="another_feature", project=project)

    # When
    with django_assert_num_queries(8):
        response = admin_client.get(base_url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_filter_using_feataure_name(
    environment, project, feature, client
):
    # Given
    Feature.objects.create(name="another_feature", project=project)
    base_url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )
    url = f"{base_url}?feature_name={feature.name}"

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["feature"] == feature.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_filter_to_show_identity_override_only(
    environment, feature, client
):
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
    res = client.get(url)

    # Then
    assert res.status_code == status.HTTP_200_OK

    # and
    assert len(res.json().get("results")) == 1

    # and
    assert res.json()["results"][0]["identity"]["identifier"] == identifier


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_only_returns_latest_versions(
    environment, feature, client
):
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
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == feature_state_v2.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_environment_feature_states_does_not_return_null_versions(
    environment, feature, client
):
    # Given
    feature_state = FeatureState.objects.get(environment=environment, feature=feature)

    FeatureState.objects.create(environment=environment, feature=feature, version=None)

    url = reverse(
        "api-v1:environments:environment-featurestates-list",
        args=[environment.api_key],
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == feature_state.id

    # Feature tests


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_default_is_archived_is_false(client, project):
    # Given - set up data
    data = {
        "name": "test feature",
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert response["is_archived"] is False


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_feature_is_archived(client, project, feature):
    # Given
    feature = Feature.objects.create(name="test feature", project=project)
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    data = {"name": "test feature", "is_archived": True}

    # When
    response = client.put(url, data=data).json()

    # Then
    assert response["is_archived"] is True


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_create_feature_states_when_feature_created(
    client, project, environment
):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

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
@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_create_feature_states_with_value_when_feature_created(
    client, project, environment, default_value
):
    # Given - set up data
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {
        "name": "test feature",
        "initial_value": default_value,
        "project": project.id,
    }

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    # check feature was created successfully
    assert Feature.objects.filter(name="test feature", project=project.id).count() == 1

    # check feature was added to environment
    assert FeatureState.objects.filter(environment=environment).count() == 1

    # check that value was correctly added to feature state
    feature_state = FeatureState.objects.filter(environment=environment).first()
    assert feature_state.get_feature_state_value() == default_value


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_delete_feature_states_when_feature_deleted(
    client, project, feature, environment
):
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )

    # When
    response = client.delete(url)

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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_returns_201_if_name_matches_regex(client, project):
    # Given
    project.feature_name_regex = "^[a-z_]{18}$"
    project.save()

    # feature name that has 18 characters
    feature_name = "valid_feature_name"

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": feature_name, "type": "FLAG", "project": project.id}

    # When
    response = client.post(url, data=data)
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_returns_400_if_name_does_not_matches_regex(client, project):
    # Given
    project.feature_name_regex = "^[a-z]{18}$"
    project.save()

    # feature name longer than 18 characters
    feature_name = "not_a_valid_feature_name"

    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": feature_name, "type": "FLAG", "project": project.id}

    # When
    response = client.post(url, data=data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["name"][0]
        == f"Feature name must match regex: {project.feature_name_regex}"
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_feature_created(client, project, environment):
    # Given
    url = reverse("api-v1:projects:project-features-list", args=[project.id])
    data = {"name": "Test feature flag", "type": "FLAG", "project": project.id}

    # When
    response = client.post(url, data=data)
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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_log_created_when_feature_updated(client, project, feature):
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
    client.put(url, data=data)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FEATURE.name
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_audit_logs_created_when_feature_deleted(client, project, feature):
    # Given
    url = reverse(
        "api-v1:projects:project-features-detail",
        args=[project.id, feature.id],
    )
    feature_states_ids = list(feature.feature_states.values_list("id", flat=True))

    # When
    client.delete(url)

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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_should_create_tags_when_feature_created(client, project, tag_one, tag_two):
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
    response = client.post(
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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_add_owners_adds_owner_when_users_not_connected(client, project):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")
    # Then
    response.status_code == status.HTTP_400_BAD_REQUEST
    response.data == ["Some users not found"]


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_add_owners_adds_owner(staff_user, admin_user, client, project):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_list_features_return_tags(client, project, feature):
    # Given
    Feature.objects.create(name="test_feature", project=project)
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()

    feature = response_json["results"][0]
    assert "tags" in feature


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_project_admin_can_create_mv_options_when_creating_feature(client, project):
    # Given
    data = {
        "name": "test_feature",
        "default_enabled": True,
        "multivariate_options": [{"type": "unicode", "string_value": "test-value"}],
    }
    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # When
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert len(response_json["multivariate_options"]) == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_feature_by_uuid(client, project, feature):
    # Given
    url = reverse("api-v1:features:get-feature-by-uuid", args=[feature.uuid])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["id"] == feature.id
    assert response.json()["uuid"] == str(feature.uuid)


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_feature_by_uuid_returns_404_if_feature_does_not_exists(client, project):
    # Given
    url = reverse("api-v1:features:get-feature-by-uuid", args=[uuid.uuid4()])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_update_feature_state_value_triggers_dynamo_rebuild(
    client, project, environment, feature, feature_state, settings, mocker
):
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
    response = client.patch(
        url,
        data=json.dumps({"feature_state_value": "new value"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    mock_dynamo_environment_wrapper.write_environments.assert_called_once()


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_segment_overrides_creates_correct_audit_log_messages(
    client, feature, segment, environment
):
    # Given
    another_segment = Segment.objects.create(
        name="Another segment", project=segment.project
    )

    feature_segments_url = reverse("api-v1:features:feature-segment-list")
    feature_states_url = reverse("api-v1:features:featurestates-list")

    # When
    # we create 2 segment overrides for the feature
    for _segment in (segment, another_segment):
        feature_segment_response = client.post(
            feature_segments_url,
            data={
                "feature": feature.id,
                "segment": _segment.id,
                "environment": environment.id,
            },
        )
        assert feature_segment_response.status_code == status.HTTP_201_CREATED
        feature_segment_id = feature_segment_response.json()["id"]
        feature_state_response = client.post(
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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_list_features_provides_information_on_number_of_overrides(
    feature,
    segment,
    segment_featurestate,
    identity,
    identity_featurestate,
    project,
    environment,
    client,
):
    # Given
    url = "%s?environment=%d" % (
        reverse("api-v1:projects:project-features-list", args=[project.id]),
        environment.id,
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["num_segment_overrides"] == 1
    assert response_json["results"][0]["num_identity_overrides"] == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_list_features_provides_segment_overrides_for_dynamo_enabled_project(
    dynamo_enabled_project, dynamo_enabled_project_environment_one, client
):
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
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["results"][0]["num_segment_overrides"] == 1
    assert response_json["results"][0]["num_identity_overrides"] is None


def test_create_segment_override_reaching_max_limit(
    admin_client, feature, segment, project, environment, settings
):
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
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Then
    # Try to create another override
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["environment"]
        == "The environment has reached the maximum allowed segments overrides limit."
    )
    assert environment.feature_segments.count() == 1


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_feature_reaching_max_limit(client, project, settings):
    # Given
    project.max_features_allowed = 1
    project.save()

    url = reverse("api-v1:projects:project-features-list", args=[project.id])

    # Now, crate the first feature
    response = client.post(url, data={"name": "test_feature", "project": project.id})
    assert response.status_code == status.HTTP_201_CREATED

    # Then
    # Try to create another feature
    response = client.post(url, data={"name": "second_feature", "project": project.id})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["project"]
        == "The Project has reached the maximum allowed features limit."
    )


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_create_segment_override_using_environment_viewset(
    client, environment, feature, feature_segment
):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response.json()["feature_state_value"] == new_value


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_create_feature_state_for_feature_from_different_project(
    client, environment, project_two_feature, feature_segment, project_two
):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["feature"][0] == "Feature does not exist in project"


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_create_feature_state_environment_is_read_only(
    client, environment, feature, feature_segment, environment_two
):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["environment"] == environment.id


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_create_feature_state_of_feature_from_different_project(
    client, environment, project_two_feature, feature_segment
):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["feature"][0] == "Feature does not exist in project"


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_create_feature_state_environment_field_is_read_only(
    client, environment, feature, feature_segment, environment_two
):
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
    response = client.post(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["environment"] == environment.id


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_update_environment_of_a_feature_state(
    client, environment, feature, feature_state, environment_two
):
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
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then - it did not change the environment field on the feature state
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["environment"][0]
        == "Cannot change the environment of a feature state"
    )


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_cannot_update_feature_of_a_feature_state(
    client, environment, feature_state, feature, identity, project
):
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
    response = client.put(url, data=json.dumps(data), content_type="application/json")

    # Then
    assert another_feature.feature_states.count() == 1
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.json()["feature"][0] == "Cannot change the feature of a feature state"
    )
