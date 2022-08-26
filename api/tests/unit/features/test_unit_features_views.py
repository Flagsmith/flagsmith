import json

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from audit.models import AuditLog, RelatedObjectType
from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from organisations.models import Organisation
from projects.models import Project, UserProjectPermission
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
    with django_assert_num_queries(7):
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
    with django_assert_num_queries(7):
        response = admin_client.get(base_url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3


@pytest.mark.parametrize(
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
)
def test_audit_log_created_when_feature_created(client, project):
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    )
    # and audit logs exists for all feature states for that feature
    assert AuditLog.objects.filter(
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        related_object_id__in=feature_states_ids,
    ).count() == len(feature_states_ids)


@pytest.mark.parametrize(
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
)
def test_add_owners_adds_owner(client, project):
    # Given
    feature = Feature.objects.create(name="Test Feature", project=project)
    user_1 = FFAdminUser.objects.create_user(email="user1@mail.com")
    user_2 = FFAdminUser.objects.create_user(email="user2@mail.com")
    url = reverse(
        "api-v1:projects:project-features-add-owners",
        args=[project.id, feature.id],
    )
    data = {"user_ids": [user_1.id, user_2.id]}

    # When
    json_response = client.post(
        url, data=json.dumps(data), content_type="application/json"
    ).json()

    # Then
    assert len(json_response["owners"]) == 2
    assert json_response["owners"][0] == {
        "id": user_1.id,
        "email": user_1.email,
        "first_name": user_1.first_name,
        "last_name": user_1.last_name,
    }
    assert json_response["owners"][1] == {
        "id": user_2.id,
        "email": user_2.email,
        "first_name": user_2.first_name,
        "last_name": user_2.last_name,
    }


@pytest.mark.parametrize(
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
    "client", [(lazy_fixture("master_api_key_client")), (lazy_fixture("admin_client"))]
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
