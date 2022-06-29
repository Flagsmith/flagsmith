import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_lazyfixture import lazy_fixture
from rest_framework import status

from environments.identities.models import Identity
from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from organisations.models import Organisation
from projects.models import Project, UserProjectPermission


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
