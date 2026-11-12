from __future__ import annotations

import pytest
from django.db.utils import IntegrityError

from environments.models import Environment
from experimentation.models import (
    ExpectedDirection,
    Experiment,
    ExperimentMetric,
    Metric,
    MetricAggregation,
)

pytestmark = pytest.mark.django_db


def _numeric_metric(
    environment: Environment, name: str = "Sessions per User"
) -> Metric:
    metric: Metric = Metric.objects.create(
        environment=environment,
        name=name,
        aggregation=MetricAggregation.COUNT,
        definition={"version": 1, "event": "session_started"},
    )
    return metric


def test_metric__defaults__mean_aggregation(environment: Environment) -> None:
    # Given a metric created without an explicit aggregation or description

    # When it is created
    metric = Metric.objects.create(
        environment=environment,
        name="Avg Duration",
        definition={"version": 1, "event": "session_ended"},
    )

    # Then it defaults to mean aggregation and an empty description
    assert metric.aggregation == MetricAggregation.MEAN
    assert metric.description == ""


def test_experiment_metric__attach__persists_direction(
    experiment: Experiment,
    environment: Environment,
) -> None:
    # Given
    metric = _numeric_metric(environment)

    # When
    em = ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # Then
    assert em in experiment.experiment_metrics.all()
    assert em.expected_direction == ExpectedDirection.INCREASE


def test_experiment_metric__same_metric_twice__raises_integrity_error(
    experiment: Experiment,
    environment: Environment,
) -> None:
    # Given
    metric = _numeric_metric(environment)
    ExperimentMetric.objects.create(
        experiment=experiment,
        metric=metric,
        expected_direction=ExpectedDirection.INCREASE,
    )

    # When / Then
    with pytest.raises(IntegrityError):
        ExperimentMetric.objects.create(
            experiment=experiment,
            metric=metric,
            expected_direction=ExpectedDirection.DECREASE,
        )


def test_metric__delete__soft_deletes_and_excludes_from_default_manager(
    environment: Environment,
) -> None:
    # Given
    metric = _numeric_metric(environment)

    # When
    metric.delete()

    # Then — default manager excludes soft-deleted (filtering by a non-pk field;
    # the soft-delete manager intentionally includes soft-deleted rows on pk lookups)
    assert not Metric.objects.filter(name=metric.name).exists()
    metric.refresh_from_db()
    assert metric.deleted_at is not None
