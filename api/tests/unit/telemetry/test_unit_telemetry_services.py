import typing

import pytest

from environments.models import Environment
from features.models import Feature
from projects.models import Project
from telemetry.services import get_resolved_ids
from telemetry.types import ResolvedIds


def test_get_resolved_ids__project_id__resolves_organisation(
    project: Project,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(1):
        resolved_ids = get_resolved_ids({"project__id": project.id})

    # Then
    assert resolved_ids == {
        "organisation__id": project.organisation_id,
        "project__id": project.id,
    }


def test_get_resolved_ids__deleted_project__resolves_nothing(
    project: Project,
) -> None:
    # Given
    project.delete()

    # When
    resolved_ids = get_resolved_ids({"project__id": project.id})

    # Then
    assert resolved_ids == {"project__id": project.id}


def test_get_resolved_ids__feature_id__resolves_project_and_organisation(
    feature: Feature,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(1):
        resolved_ids = get_resolved_ids({"feature__id": feature.id})

    # Then
    assert resolved_ids == {
        "feature__id": feature.id,
        "organisation__id": feature.project.organisation_id,
        "project__id": feature.project_id,
    }


def test_get_resolved_ids__feature_and_project_ids__resolves_organisation_only(
    feature: Feature,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(1):
        resolved_ids = get_resolved_ids(
            {"feature__id": feature.id, "project__id": feature.project_id}
        )

    # Then
    assert resolved_ids == {
        "feature__id": feature.id,
        "organisation__id": feature.project.organisation_id,
        "project__id": feature.project_id,
    }


def test_get_resolved_ids__environment_api_key__resolves_environment_project_and_organisation(
    environment: Environment,
    feature: Feature,
    django_assert_num_queries: typing.Any,
) -> None:
    # Given / When
    with django_assert_num_queries(1):
        resolved_ids = get_resolved_ids(
            {"environment__api_key": environment.api_key, "feature__id": feature.id}
        )

    # Then
    assert resolved_ids == {
        "environment__api_key": environment.api_key,
        "environment__id": environment.id,
        "feature__id": feature.id,
        "organisation__id": environment.project.organisation_id,
        "project__id": environment.project_id,
    }


@pytest.mark.parametrize(
    "ids",
    [
        {"environment__api_key": "unknown"},
        {"feature__id": 404},
        {"project__id": 404},
    ],
)
def test_get_resolved_ids__unknown_entities__resolves_nothing(
    db: None,
    ids: ResolvedIds,
) -> None:
    # Given / When
    resolved_ids = get_resolved_ids(ids)

    # Then
    assert resolved_ids == ids


def test_get_resolved_ids__complete_ids__queries_nothing() -> None:
    # Given
    ids: ResolvedIds = {
        "environment__api_key": "key",
        "environment__id": 1,
        "feature__id": 2,
        "organisation__id": 3,
        "project__id": 4,
    }

    # When
    # NOTE: Without database access, any query would fail the test
    resolved_ids = get_resolved_ids(ids)

    # Then
    assert resolved_ids == ids
    assert resolved_ids is not ids
