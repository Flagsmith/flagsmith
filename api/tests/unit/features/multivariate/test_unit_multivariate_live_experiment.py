from typing import Any

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from experimentation.models import Experiment, ExperimentStatus
from features.constants import LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from projects.models import Project


@pytest.fixture(params=[ExperimentStatus.RUNNING, ExperimentStatus.PAUSED])
def live_experiment(
    request: pytest.FixtureRequest,
    environment: Environment,
    multivariate_feature: Feature,
) -> Experiment:
    return Experiment.objects.create(  # type: ignore[no-any-return]
        environment=environment,
        feature=multivariate_feature,
        name="live experiment",
        hypothesis="new option wins",
        status=request.param,
    )


def _options_url(project: Project, feature: Feature) -> str:
    return f"/api/v1/projects/{project.id}/features/{feature.id}/mv-options/"


def _expected_error(experiment: Experiment) -> dict[str, str]:
    return {
        "detail": LIVE_EXPERIMENT_MV_OPTIONS_MESSAGE.format(
            environment=experiment.environment.name
        )
    }


def _dashboard_option_payload(option: MultivariateFeatureOption) -> dict[str, Any]:
    # What the dashboard PUTs for every existing option on each save.
    return {
        "id": option.id,
        "type": option.type,
        "string_value": option.string_value,
        "integer_value": option.integer_value,
        "boolean_value": option.boolean_value,
        "key": option.key,
        "default_percentage_allocation": 0,
        "feature": option.feature_id,
    }


def test_create_mv_option__live_experiment__returns_400(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
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
    assert response.json() == _expected_error(live_experiment)
    assert multivariate_feature.multivariate_options.count() == 3


def test_update_mv_option__running_experiment_unchanged_payload__returns_200(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.first()
    assert option is not None
    option.key = "variation-a"
    option.save()

    # When
    response = admin_client.put(
        f"{_options_url(project, multivariate_feature)}{option.id}/",
        data=_dashboard_option_payload(option),
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    option.refresh_from_db()
    assert option.string_value == "multivariate option for 30% of users."
    assert option.key == "variation-a"


def test_update_mv_option__running_experiment_default_allocation_only__returns_200(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.first()
    assert option is not None
    option.key = "variation-a"
    option.save()
    payload = {**_dashboard_option_payload(option), "default_percentage_allocation": 10}

    # When
    response = admin_client.put(
        f"{_options_url(project, multivariate_feature)}{option.id}/",
        data=payload,
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    option.refresh_from_db()
    assert option.default_percentage_allocation == 10
    assert option.string_value == "multivariate option for 30% of users."
    assert option.key == "variation-a"


@pytest.mark.parametrize(
    "option_kwargs, patch",
    [
        (
            {"type": "unicode", "string_value": "original", "key": "variation-a"},
            {"string_value": "edited"},
        ),
        (
            {"type": "unicode", "string_value": "original", "key": "variation-a"},
            {"key": "edited-key"},
        ),
        (
            {"type": "unicode", "string_value": "original", "key": "variation-a"},
            {"type": "int", "integer_value": 1, "string_value": None},
        ),
        (
            {"type": "int", "integer_value": 42, "key": "variation-int"},
            {"integer_value": 99},
        ),
        (
            {"type": "bool", "boolean_value": True, "key": "variation-bool"},
            {"boolean_value": False},
        ),
    ],
)
def test_update_mv_option__running_experiment_changed_field__returns_400(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
    option_kwargs: dict[str, Any],
    patch: dict[str, Any],
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.first()
    assert option is not None
    option.type = option_kwargs["type"]
    option.string_value = option_kwargs.get("string_value")
    option.integer_value = option_kwargs.get("integer_value")
    option.boolean_value = option_kwargs.get("boolean_value")
    option.key = option_kwargs["key"]
    option.save()
    payload = {**_dashboard_option_payload(option), **patch}

    # When
    response = admin_client.put(
        f"{_options_url(project, multivariate_feature)}{option.id}/",
        data=payload,
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == _expected_error(live_experiment)
    option.refresh_from_db()
    assert option.type == option_kwargs["type"]
    assert option.string_value == option_kwargs.get("string_value")
    assert option.integer_value == option_kwargs.get("integer_value")
    assert option.boolean_value == option_kwargs.get("boolean_value")
    assert option.key == option_kwargs["key"]


@pytest.mark.parametrize(
    "experiment_status", [ExperimentStatus.CREATED, ExperimentStatus.COMPLETED]
)
def test_update_mv_option__experiment_not_running__returns_200(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    multivariate_feature: Feature,
    experiment_status: str,
) -> None:
    # Given
    Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="inactive experiment",
        hypothesis="new option wins",
        status=experiment_status,
    )
    option = multivariate_feature.multivariate_options.first()
    assert option is not None
    payload = {**_dashboard_option_payload(option), "string_value": "edited"}

    # When
    response = admin_client.put(
        f"{_options_url(project, multivariate_feature)}{option.id}/",
        data=payload,
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    option.refresh_from_db()
    assert option.string_value == "edited"


def test_save_feature_value__experiment_running_in_other_environment__returns_200(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    environment_two: Environment,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    options = list(multivariate_feature.multivariate_options.order_by("id"))
    feature_state_a = environment.feature_states.get(
        feature=multivariate_feature, identity=None, feature_segment=None
    )
    feature_state_b = environment_two.feature_states.get(
        feature=multivariate_feature, identity=None, feature_segment=None
    )
    allocations_a = {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in feature_state_a.multivariate_feature_state_values.all()
    }
    new_allocations_b = dict(zip((option.id for option in options), (10, 20, 30)))

    # When
    option_responses = [
        admin_client.put(
            f"{_options_url(project, multivariate_feature)}{option.id}/",
            data=_dashboard_option_payload(option),
            format="json",
        )
        for option in options
    ]
    feature_state_response = admin_client.put(
        reverse(
            "api-v1:environments:environment-featurestates-detail",
            args=[environment_two.api_key, feature_state_b.id],
        ),
        data={
            "id": feature_state_b.id,
            "feature_state_value": "new control",
            "enabled": True,
            "feature": multivariate_feature.id,
            "environment": environment_two.id,
            "identity": None,
            "feature_segment": None,
            "multivariate_feature_state_values": [
                {
                    "id": mv.id,
                    "multivariate_feature_option": mv.multivariate_feature_option_id,
                    "percentage_allocation": new_allocations_b[
                        mv.multivariate_feature_option_id
                    ],
                }
                for mv in feature_state_b.multivariate_feature_state_values.all()
            ],
        },
        format="json",
    )

    # Then
    assert [r.status_code for r in option_responses] == [status.HTTP_200_OK] * 3
    assert feature_state_response.status_code == status.HTTP_200_OK

    feature_state_b.refresh_from_db()
    assert feature_state_b.get_feature_state_value() == "new control"
    assert {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in feature_state_b.multivariate_feature_state_values.all()
    } == new_allocations_b

    feature_state_a.refresh_from_db()
    assert feature_state_a.get_feature_state_value() == "control"
    assert {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in feature_state_a.multivariate_feature_state_values.all()
    } == allocations_a


def test_update_mv_option__moving_to_live_experiment__returns_400(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    multivariate_feature: Feature,
) -> None:
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

    experiment = Experiment.objects.create(
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
    assert response.json() == _expected_error(experiment)
    option.refresh_from_db()
    assert option.feature == other_feature
    assert multivariate_feature.multivariate_options.count() == 3


def test_create_mv_option__body_feature_mismatches_url__returns_400(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
) -> None:
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


def test_delete_mv_option__live_experiment__returns_400(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.first()
    assert option is not None

    # When
    response = admin_client.delete(
        f"{_options_url(project, multivariate_feature)}{option.id}/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == _expected_error(live_experiment)
    assert MultivariateFeatureOption.objects.filter(id=option.id).exists()


def test_create_mv_option__no_live_experiment__returns_201(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
) -> None:
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


def test_update_feature__live_experiment__changed_mv_options_returns_400(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
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
    assert response.json() == _expected_error(live_experiment)


def test_update_feature__live_experiment__unchanged_keyed_options_preserved(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    keyed_option = multivariate_feature.multivariate_options.first()
    assert keyed_option is not None
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
            "default_percentage_allocation": 0,
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


def test_update_feature__live_experiment__default_allocation_only_persisted(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    options = list(multivariate_feature.multivariate_options.order_by("id"))
    options[0].key = "stable-option"
    options[0].save()
    feature_state = environment.feature_states.get(
        feature=multivariate_feature, identity=None, feature_segment=None
    )
    env_allocations_before = {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in feature_state.multivariate_feature_state_values.all()
    }
    url = f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/"
    new_default_allocations = [15.0, 25.0, 35.0]
    payload = [
        {
            "id": option.id,
            "type": option.type,
            "string_value": option.string_value,
            "default_percentage_allocation": new_alloc,
        }
        for option, new_alloc in zip(options, new_default_allocations)
    ]

    # When
    response = admin_client.patch(
        url,
        data={"multivariate_options": payload},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    returned_allocations = {
        item["id"]: item["default_percentage_allocation"]
        for item in response.json()["multivariate_options"]
    }
    for option, expected_alloc in zip(options, new_default_allocations):
        option.refresh_from_db()
        assert option.default_percentage_allocation == expected_alloc
        assert returned_allocations[option.id] == expected_alloc

    options[0].refresh_from_db()
    assert options[0].key == "stable-option"
    assert {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in feature_state.multivariate_feature_state_values.all()
    } == env_allocations_before


@pytest.mark.parametrize("identifier_field", ["id", "uuid", "key"])
def test_update_feature__live_experiment__duplicate_values_matched_by_identifier(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
    identifier_field: str,
) -> None:
    # Given
    options = list(multivariate_feature.multivariate_options.order_by("id"))
    options[0].string_value = "shared-value"
    options[0].key = "variant-first"
    options[0].default_percentage_allocation = 10.0
    options[0].save()
    options[1].string_value = "shared-value"
    options[1].key = "variant-second"
    options[1].default_percentage_allocation = 20.0
    options[1].save()
    url = f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/"

    def _identifier(opt: MultivariateFeatureOption) -> Any:
        value = getattr(opt, identifier_field)
        return str(value) if identifier_field == "uuid" else value

    # Submit the duplicate-value options in reversed order so positional
    # matching would assign allocations to the wrong option.
    payload = [
        {
            identifier_field: _identifier(options[1]),
            "type": options[1].type,
            "string_value": options[1].string_value,
            "default_percentage_allocation": 35.0,
        },
        {
            identifier_field: _identifier(options[0]),
            "type": options[0].type,
            "string_value": options[0].string_value,
            "default_percentage_allocation": 15.0,
        },
        {
            identifier_field: _identifier(options[2]),
            "type": options[2].type,
            "string_value": options[2].string_value,
            "default_percentage_allocation": 25.0,
        },
    ]

    # When
    response = admin_client.patch(
        url,
        data={"multivariate_options": payload},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    options[0].refresh_from_db()
    options[1].refresh_from_db()
    options[2].refresh_from_db()
    assert options[0].default_percentage_allocation == 15.0
    assert options[1].default_percentage_allocation == 35.0
    assert options[2].default_percentage_allocation == 25.0


def test_update_feature__live_experiment__ambiguous_duplicate_values_without_id_returns_400(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
    live_experiment: Experiment,
) -> None:
    # Given
    options = list(multivariate_feature.multivariate_options.order_by("id"))
    options[0].string_value = "shared-value"
    options[0].key = "variant-first"
    options[0].default_percentage_allocation = 10.0
    options[0].save()
    options[1].string_value = "shared-value"
    options[1].key = "variant-second"
    options[1].default_percentage_allocation = 20.0
    options[1].save()
    url = f"/api/v1/projects/{project.id}/features/{multivariate_feature.id}/"
    payload = [
        {
            "type": options[1].type,
            "string_value": options[1].string_value,
            "default_percentage_allocation": 35.0,
        },
        {
            "type": options[0].type,
            "string_value": options[0].string_value,
            "default_percentage_allocation": 15.0,
        },
        {
            "type": options[2].type,
            "string_value": options[2].string_value,
            "default_percentage_allocation": 25.0,
        },
    ]

    # When
    response = admin_client.patch(
        url,
        data={"multivariate_options": payload},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "multivariate_options" in response.json()
    options[0].refresh_from_db()
    options[1].refresh_from_db()
    assert options[0].default_percentage_allocation == 10.0
    assert options[1].default_percentage_allocation == 20.0


def test_delete_mv_option__concurrent_move_to_live_experiment__relocks_and_returns_400(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    multivariate_feature: Feature,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    source_feature = Feature.objects.create(name="source feature", project=project)
    option = MultivariateFeatureOption.objects.create(
        feature=source_feature,
        type="unicode",
        string_value="moving option",
        default_percentage_allocation=0,
    )
    experiment = Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="live experiment",
        hypothesis="new option wins",
        status=ExperimentStatus.RUNNING,
    )
    locked_batches: list[list[int]] = []
    original_select_for_update = Feature.objects.select_for_update

    def _simulating_concurrent_move(*args: Any, **kwargs: Any) -> Any:
        qs = original_select_for_update(*args, **kwargs)
        original_filter = qs.filter

        def _filter(*f_args: Any, **f_kwargs: Any) -> Any:
            filtered = original_filter(*f_args, **f_kwargs)
            pks = f_kwargs.get("pk__in")
            if pks is not None:
                locked_batches.append(list(pks))
                if len(locked_batches) == 1:
                    MultivariateFeatureOption.objects.filter(pk=option.pk).update(
                        feature=multivariate_feature
                    )
            return filtered

        qs.filter = _filter
        return qs

    monkeypatch.setattr(
        Feature.objects, "select_for_update", _simulating_concurrent_move
    )

    # When
    response = admin_client.delete(
        f"{_options_url(project, source_feature)}{option.id}/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == _expected_error(experiment)
    assert locked_batches == [[source_feature.id], [multivariate_feature.id]]
    assert MultivariateFeatureOption.objects.filter(id=option.id).exists()


def test_update_mv_option__concurrent_move_to_live_experiment__relocks_and_returns_400(
    admin_client: APIClient,
    project: Project,
    environment: Environment,
    multivariate_feature: Feature,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    source_feature = Feature.objects.create(name="source feature", project=project)
    option = MultivariateFeatureOption.objects.create(
        feature=source_feature,
        type="unicode",
        string_value="moving option",
        default_percentage_allocation=0,
    )
    experiment = Experiment.objects.create(
        environment=environment,
        feature=multivariate_feature,
        name="live experiment",
        hypothesis="new option wins",
        status=ExperimentStatus.RUNNING,
    )
    locked_batches: list[list[int]] = []
    original_select_for_update = Feature.objects.select_for_update

    def _simulating_concurrent_move(*args: Any, **kwargs: Any) -> Any:
        qs = original_select_for_update(*args, **kwargs)
        original_filter = qs.filter

        def _filter(*f_args: Any, **f_kwargs: Any) -> Any:
            filtered = original_filter(*f_args, **f_kwargs)
            pks = f_kwargs.get("pk__in")
            if pks is not None:
                locked_batches.append(list(pks))
                if len(locked_batches) == 1:
                    MultivariateFeatureOption.objects.filter(pk=option.pk).update(
                        feature=multivariate_feature
                    )
            return filtered

        qs.filter = _filter
        return qs

    monkeypatch.setattr(
        Feature.objects, "select_for_update", _simulating_concurrent_move
    )

    # When
    response = admin_client.put(
        f"{_options_url(project, source_feature)}{option.id}/",
        data={**_dashboard_option_payload(option), "string_value": "edited"},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == _expected_error(experiment)
    assert locked_batches == [[source_feature.id], [multivariate_feature.id]]
    option.refresh_from_db()
    assert option.string_value == "moving option"
