import threading
import time
from unittest import mock

import pytest
from django.db import connection, connections, transaction
from django.test.utils import CaptureQueriesContext
from pytest_django import DjangoAssertNumQueries

from environments.models import Environment
from features.dependencies.exceptions import CircularDependencyError
from features.dependencies.models import SegmentFlagReference
from features.dependencies.services import (
    FLAG_DEPENDENCIES_ADVISORY_LOCK_NAMESPACE,
    validate_segment_flag_dependencies,
)
from features.models import Feature, FeatureSegment, FeatureState
from projects.models import Project
from segments.models import Segment


@pytest.mark.parametrize("environment_count", [1, 2, 3])
def test_validate_segment_flag_dependencies__overrides_across_environments__queries_once_per_environment(
    django_assert_num_queries: DjangoAssertNumQueries,
    environment_count: int,
    project: Project,
    segment: Segment,
) -> None:
    # Given
    for environment_index in range(environment_count):
        environment = Environment.objects.create(
            name=f"environment{environment_index}", project=project
        )
        for feature_name in ["chicken", "egg", "hen"]:
            feature, _ = Feature.objects.get_or_create(
                name=feature_name, project=project
            )
            feature_segment = FeatureSegment.objects.create(
                feature=feature, segment=segment, environment=environment
            )
            FeatureState.objects.create(
                feature=feature,
                environment=environment,
                feature_segment=feature_segment,
            )
    SegmentFlagReference.objects.create(
        segment=segment,
        prerequisite_feature=Feature.objects.create(name="corn", project=project),
        condition_json_path="$[0].conditions[0]",
    )

    # When / Then
    with django_assert_num_queries(3 + environment_count):
        validate_segment_flag_dependencies(segment)


def test_validate_segment_flag_dependencies__no_references__skips(
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
    feature: Feature,
    segment: Segment,
) -> None:
    # Given
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )

    # When / Then
    with django_assert_num_queries(2):
        validate_segment_flag_dependencies(segment)


def _create_override(
    *, feature: Feature, segment: Segment, environment: Environment
) -> None:
    feature_segment = FeatureSegment.objects.create(
        feature=feature, segment=segment, environment=environment
    )
    FeatureState.objects.create(
        feature=feature, environment=environment, feature_segment=feature_segment
    )


def test_validate_segment_flag_dependencies__segment_with_references__locks_project_before_reading(
    environment: Environment,
    feature: Feature,
    project: Project,
    segment: Segment,
) -> None:
    # Given
    _create_override(feature=feature, segment=segment, environment=environment)
    SegmentFlagReference.objects.create(
        segment=segment,
        prerequisite_feature=Feature.objects.create(name="corn", project=project),
        condition_json_path="$[0].conditions[0]",
    )

    # When
    with CaptureQueriesContext(connection) as captured:
        validate_segment_flag_dependencies(segment)

    # Then
    assert captured.captured_queries[0]["sql"] == (
        "SELECT pg_advisory_xact_lock("
        f"{FLAG_DEPENDENCIES_ADVISORY_LOCK_NAMESPACE}, {project.id})"
    )


def test_validate_segment_flag_dependencies__no_references__still_locks_project(
    project: Project,
    segment: Segment,
) -> None:
    # Given
    assert not SegmentFlagReference.objects.filter(segment=segment).exists()

    # When
    with CaptureQueriesContext(connection) as captured:
        validate_segment_flag_dependencies(segment)

    # Then
    assert captured.captured_queries[0]["sql"] == (
        "SELECT pg_advisory_xact_lock("
        f"{FLAG_DEPENDENCIES_ADVISORY_LOCK_NAMESPACE}, {project.id})"
    )


def test_validate_segment_flag_dependencies__non_postgresql_database__locks_project_row(
    project: Project,
    segment: Segment,
) -> None:
    # Given
    oracle_connection = mock.Mock(in_atomic_block=True, vendor="oracle")

    # When
    with (
        mock.patch.object(
            transaction, "get_connection", return_value=oracle_connection
        ),
        CaptureQueriesContext(connection) as captured,
    ):
        validate_segment_flag_dependencies(segment)

    # Then
    lock_sql = captured.captured_queries[0]["sql"]
    assert 'FROM "projects_project"' in lock_sql
    assert f'"projects_project"."id" = {project.id}' in lock_sql
    assert lock_sql.endswith("FOR UPDATE")


@pytest.mark.django_db(transaction=True)
def test_validate_segment_flag_dependencies__outside_transaction__raises(
    segment: Segment,
) -> None:
    # Given
    assert not connection.in_atomic_block

    # When / Then
    with pytest.raises(RuntimeError, match="inside a transaction"):
        validate_segment_flag_dependencies(segment)


@pytest.mark.django_db(transaction=True)
def test_validate_segment_flag_dependencies__concurrent_opposite_edges__rejects_the_later(
    environment: Environment,
    project: Project,
) -> None:
    # Given
    chicken = Feature.objects.create(name="chicken", project=project)
    egg = Feature.objects.create(name="egg", project=project)
    needs_egg = Segment.objects.create(name="needs_egg", project=project)
    needs_chicken = Segment.objects.create(name="needs_chicken", project=project)
    SegmentFlagReference.objects.create(
        segment=needs_egg,
        prerequisite_feature=egg,
        condition_json_path="$[0].conditions[0]",
    )
    SegmentFlagReference.objects.create(
        segment=needs_chicken,
        prerequisite_feature=chicken,
        condition_json_path="$[0].conditions[0]",
    )
    first_validated = threading.Event()
    errors: list[Exception] = []

    def add_edge(feature: Feature, segment: Segment) -> None:
        try:
            with transaction.atomic():
                _create_override(
                    feature=feature, segment=segment, environment=environment
                )
                validate_segment_flag_dependencies(segment)
                if feature == chicken:
                    first_validated.set()
                    _wait_for_advisory_lock_waiter()
        except Exception as error:
            errors.append(error)
        finally:
            connections.close_all()

    first = threading.Thread(target=add_edge, args=(chicken, needs_egg))
    second = threading.Thread(target=add_edge, args=(egg, needs_chicken))

    # When
    first.start()
    assert first_validated.wait(timeout=5)
    second.start()
    first.join(timeout=10)
    second.join(timeout=10)

    # Then
    assert [type(error) for error in errors] == [CircularDependencyError]
    assert not FeatureSegment.objects.filter(feature=egg).exists()


def _wait_for_advisory_lock_waiter(timeout: float = 5) -> None:
    """Hold the transaction open until another one waits on the project lock."""
    deadline = time.monotonic() + timeout
    with connection.cursor() as cursor:
        while time.monotonic() < deadline:
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM pg_locks"
                " WHERE locktype = 'advisory' AND classid = %s AND NOT granted)",
                [FLAG_DEPENDENCIES_ADVISORY_LOCK_NAMESPACE],
            )
            if cursor.fetchone()[0]:
                return
            time.sleep(0.01)
