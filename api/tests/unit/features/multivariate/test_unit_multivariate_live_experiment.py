import pytest
from rest_framework import status
from rest_framework.test import APIClient

from experimentation.models import Experiment, ExperimentStatus
from features.constants import LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from projects.models import Project


@pytest.fixture()
def live_experiment(environment, multivariate_feature):  # type: ignore[no-untyped-def]
    return Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="live experiment",
        hypothesis="new option wins",
        status=ExperimentStatus.RUNNING,
    )


def _options_url(project: Project, feature: Feature) -> str:
    return f"/api/v1/projects/{project.id}/features/{feature.id}/mv-options/"


def test_create_mv_option__live_experiment__returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature, live_experiment
):
    # Given
    # When
    response = admin_client.post(
        _options_url(project, multivariate_feature),
        data={
            "feature": multivariate_feature.id,
            "type": "unicode",
            "string_value": "new option",
            "default_percentage_allocation": 0,
            "key": "new",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE in str(response.json())
    assert multivariate_feature.multivariate_options.count() == 3


def test_update_mv_option__live_experiment__returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature, live_experiment
):
    # Given
    option = multivariate_feature.multivariate_options.first()

    # When
    response = admin_client.put(
        f"{_options_url(project, multivariate_feature)}{option.id}/",
        data={
            "feature": multivariate_feature.id,
            "type": "unicode",
            "string_value": "edited",
            "default_percentage_allocation": option.default_percentage_allocation,
            "key": option.key,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    option.refresh_from_db()
    assert option.string_value != "edited"


def test_update_mv_option__moving_to_live_experiment__returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, environment, multivariate_feature
):
    # Given
    other_feature = Feature.objects.create(name="other feature", project=project)
    option = MultivariateFeatureOption.objects.create(
        feature=other_feature,
        type="unicode",
        string_value="source option",
        default_percentage_allocation=0,
    )
    for existing_option in multivariate_feature.multivariate_options.all():
        existing_option.default_percentage_allocation = 0
        existing_option.save()

    Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="live experiment",
        hypothesis="new option wins",
        status=ExperimentStatus.RUNNING,
    )

    # When
    response = admin_client.put(
        f"{_options_url(project, other_feature)}{option.id}/",
        data={
            "feature": multivariate_feature.id,
            "type": option.type,
            "string_value": option.string_value,
            "default_percentage_allocation": option.default_percentage_allocation,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    option.refresh_from_db()
    assert option.feature == other_feature
    assert multivariate_feature.multivariate_options.count() == 3


def test_create_mv_option__body_feature_mismatches_url__returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature
):
    # Given
    other_feature = Feature.objects.create(name="other feature", project=project)

    # When
    response = admin_client.post(
        _options_url(project, multivariate_feature),
        data={"feature": other_feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Feature must match the URL." in str(response.json())
    assert other_feature.multivariate_options.count() == 0


def test_delete_mv_option__live_experiment__returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature, live_experiment
):
    # Given
    option = multivariate_feature.multivariate_options.first()

    # When
    response = admin_client.delete(
        f"{_options_url(project, multivariate_feature)}{option.id}/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert MultivariateFeatureOption.objects.filter(id=option.id).exists()


def test_create_mv_option__no_live_experiment__not_blocked_by_experiment_check(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature
):
    # Given
    # When
    response = admin_client.post(
        _options_url(project, multivariate_feature),
        data={
            "feature": multivariate_feature.id,
            "type": "unicode",
            "string_value": "new option",
            "default_percentage_allocation": 0,
            "key": "new",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_update_feature__live_experiment__changed_mv_options_returns_400(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature, live_experiment
):
    # Given
    url = f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/"
    options = [
        {
            "type": "unicode",
            "string_value": "changed",
            "default_percentage_allocation": 100,
        },
    ]

    # When
    response = admin_client.patch(
        url, data={"multivariate_options": options}, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE in str(response.json())


def test_update_feature__live_experiment__unchanged_keyed_options_preserved(  # type: ignore[no-untyped-def]
    admin_client: APIClient, project, multivariate_feature, live_experiment
):
    # Given
    keyed_option = multivariate_feature.multivariate_options.first()
    keyed_option.key = "stable-option"
    keyed_option.save()
    url = f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/"
    stored_option_ids = list(
        multivariate_feature.multivariate_options.values_list("id", flat=True)
    )
    unchanged = [
        {
            "type": option.type,
            "string_value": option.string_value,
            "default_percentage_allocation": option.default_percentage_allocation,
        }
        for option in multivariate_feature.multivariate_options.all()
    ]

    # When
    response = admin_client.patch(
        url,
        data={
            "description": "only metadata changed",
            "multivariate_options": unchanged,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    keyed_option.refresh_from_db()
    assert keyed_option.key == "stable-option"
    assert (
        list(multivariate_feature.multivariate_options.values_list("id", flat=True))
        == stored_option_ids
    )
