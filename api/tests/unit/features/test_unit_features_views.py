from django.urls import reverse
from rest_framework import status

from environments.models import Environment
from features.feature_types import MULTIVARIATE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from organisations.models import Organisation
from projects.models import Project, UserProjectPermission


def test_list_feature_states_from_simple_view_set(
    environment, feature, admin_user, admin_client, django_assert_num_queries
):
    # Given
    url = reverse("api-v1:features:featurestates-list")

    # add another feature
    Feature.objects.create(name="another_feature", project=environment.project)

    # add another organisation with a project, environment and feature
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
        name="mv_feature", project=another_project, type=MULTIVARIATE
    )
    MultivariateFeatureOption.objects.create(
        feature=mv_feature,
        default_percentage_allocation=10,
        type="unicode",
        string_value="foo",
    )

    # When
    with django_assert_num_queries(4):
        response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 4


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
    with django_assert_num_queries(5):
        response = admin_client.get(base_url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert response_json["count"] == 3
