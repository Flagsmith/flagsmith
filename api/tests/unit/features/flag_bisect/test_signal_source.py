from datetime import timedelta

import pytest
from common.environments.permissions import VIEW_ENVIRONMENT
from django.urls import reverse
from django.utils import timezone
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from core.dataclasses import AuthorData
from environments.models import Environment
from experimentation.models import (
    Experiment,
    ExperimentStatus,
    SDKExperimentationEvent,
    WarehouseConnection,
    WarehouseType,
)
from experimentation.warehouses.constants import FLAGSMITH_DATABASE_SOURCE
from features.flag_bisect import services
from features.flag_bisect.models import (
    Incident,
    IncidentState,
    Probe,
    SignalBucket,
    SignalSource,
)
from features.future.services import update_flag
from features.models import Feature
from projects.models import Project
from segments.models import Segment
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db

NOW = "2026-11-27T10:00:00Z"


@pytest.fixture(autouse=True)
def flag_bisect_enabled(settings: SettingsWrapper) -> None:
    settings.FLAG_BISECT_ENABLED = True


def _event(
    environment: Environment,
    event: str,
    identifier: str,
    seconds_ago: float,
) -> SDKExperimentationEvent:
    created: SDKExperimentationEvent = SDKExperimentationEvent.objects.create(
        environment_key=environment.api_key,
        event=event,
        identifier=identifier,
        timestamp=timezone.now() - timedelta(seconds=seconds_ago),
    )
    return created


def _source(environment: Environment) -> SignalSource:
    return SignalSource.objects.create(
        environment=environment,
        failure_event="checkout_failed",
        success_event="checkout_completed",
    )


def test_set_signal_source__events_older_than_look_back__starts_after_them(
    environment: Environment,
    freezer: FrozenDateTimeFactory,
    log: StructuredLogCapture,
) -> None:
    # Given
    freezer.move_to(NOW)
    old = _event(environment, "checkout_failed", "a", seconds_ago=3600)
    _event(environment, "checkout_failed", "b", seconds_ago=60)

    # When
    source = services.set_signal_source(
        environment, "checkout_failed", "checkout_completed"
    )

    # Then
    assert source.last_event_id == old.id
    assert log.has("signal_source.saved", environment__id=environment.id)


def test_set_signal_source__existing_source__keeps_its_place(
    environment: Environment,
) -> None:
    # Given
    existing = _source(environment)
    SignalSource.objects.filter(pk=existing.pk).update(last_event_id=42)

    # When
    source = services.set_signal_source(environment, "error", "ok")

    # Then
    assert (source.pk, source.last_event_id) == (existing.pk, 42)
    assert (source.failure_event, source.success_event) == ("error", "ok")


def test_ingest_experimentation_events__mixed_events__counts_outcomes_by_event_minute(
    environment: Environment,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    freezer.move_to(NOW)
    source = _source(environment)
    _event(environment, "checkout_failed", "a", seconds_ago=90)
    _event(environment, "checkout_completed", "b", seconds_ago=90)
    _event(environment, "checkout_completed", "c", seconds_ago=10)
    _event(environment, "page_view", "d", seconds_ago=10)
    _event(environment, "checkout_failed", "", seconds_ago=10)
    _event(environment, "checkout_failed", "e", seconds_ago=3600)
    last = _event(environment, "checkout_failed", "f", seconds_ago=-60)

    # When
    counted = services.ingest_experimentation_events(source)

    # Then
    assert counted == 4
    buckets = {
        b.minute.strftime("%H:%M"): (b.total, b.failures)
        for b in SignalBucket.objects.filter(environment=environment)
    }
    # The event from a clock running a minute ahead counts now, not never.
    assert buckets == {"09:58": (2, 1), "09:59": (1, 0), "10:00": (1, 1)}
    source.refresh_from_db()
    assert source.last_event_id == last.id
    assert services.ingest_experimentation_events(source) == 0


def test_ingest_experimentation_events__during_a_probe__splits_cohorts_after_settling(
    environment: Environment,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    freezer.move_to(NOW)
    source = _source(environment)
    incident = Incident.objects.create(
        environment=environment,
        state=IncidentState.PROBING,
        onset_at=timezone.now() - timedelta(minutes=10),
        baseline_rate=0.01,
        regression_rate=0.09,
        canary_percent=50,
        canary_segment=Segment.objects.create(
            name="canary", project=environment.project
        ),
    )
    probe = Probe.objects.create(
        incident=incident,
        round=1,
        kind=Probe.Kind.BISECT,
        started_at=timezone.now() - timedelta(minutes=4),
        settles_at=timezone.now() - timedelta(seconds=150),
    )
    # Before settling, in a minute that straddles it, and after it.
    _event(environment, "checkout_failed", "early", seconds_ago=200)
    _event(environment, "checkout_failed", "straddle", seconds_ago=130)
    _event(environment, "checkout_failed", "straddle-2", seconds_ago=170)
    identifiers = [f"user-{i}" for i in range(40)]
    for identifier in identifiers:
        _event(environment, "checkout_completed", identifier, seconds_ago=30)

    # When
    services.ingest_experimentation_events(source)

    # Then
    probe.refresh_from_db()
    assert probe.canary_total + probe.main_total == len(identifiers)
    assert probe.canary_failures + probe.main_failures == 0
    assert probe.canary_total == sum(
        services.in_canary(environment, incident.canary_segment_id or 0, 50, identifier)
        for identifier in identifiers
    )


def test_run_swarm__environment_with_a_signal_source__reads_its_events(
    environment: Environment,
) -> None:
    # Given
    _source(environment)
    _event(environment, "checkout_failed", "a", seconds_ago=5)

    # When
    services.run_swarm()

    # Then
    assert SignalBucket.objects.get(environment=environment).failures == 1


def _change(
    environment: Environment, feature: Feature, admin_user: FFAdminUser
) -> None:
    update_flag(
        environment=environment,
        feature=feature,
        changes={"environment_default": {"enabled": True}},
        replace=False,
        author=AuthorData(user=admin_user),
        overwrite_system_segment_overrides=False,
    )


@pytest.mark.parametrize("all_experimented", [False, True])
def test_investigate__flag_in_a_running_experiment__is_left_alone(
    environment: Environment,
    project: Project,
    admin_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
    all_experimented: bool,
) -> None:
    # Given
    freezer.move_to(NOW)
    tested = Feature.objects.create(name="pricing_test", project=project)
    other = Feature.objects.create(name="new_tax_engine", project=project)
    freezer.tick(timedelta(seconds=1))
    _change(environment, tested, admin_user)
    if not all_experimented:
        _change(environment, other, admin_user)
    Experiment.objects.create(
        environment=environment,
        feature=tested,
        name="Pricing",
        hypothesis="Cheaper wins",
        status=ExperimentStatus.RUNNING,
    )
    freezer.tick(timedelta(minutes=2))
    incident = Incident.objects.create(
        environment=environment,
        state=IncidentState.INVESTIGATING,
        onset_at=timezone.now() - timedelta(minutes=1),
        baseline_rate=0.01,
        regression_rate=0.09,
    )

    # When
    services._investigate(incident, timezone.now())

    # Then
    incident.refresh_from_db()
    suspects = [s.feature.name for s in incident.suspects.all()]
    texts = [m.text for m in incident.messages.all()]
    assert (
        "Left alone because an experiment is running on them: pricing_test. "
        "Pause or complete the experiment to include them." in texts
    )
    if all_experimented:
        assert incident.state == IncidentState.NOT_A_FLAG_CHANGE
        assert suspects == []
    else:
        assert incident.state == IncidentState.AWAITING_APPROVAL
        assert suspects == ["new_tax_engine"]


def _url(environment: Environment) -> str:
    return reverse(
        "api-v1:environments:flag-bisect:signal-source",
        args=[environment.api_key],
    )


def test_signal_source_view__nothing_set__reports_none_and_where_events_go(
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
    WarehouseConnection.objects.create(
        environment=environment,
        warehouse_type=WarehouseType.POSTGRES,
        name="Flagsmith database",
        config={"source": FLAGSMITH_DATABASE_SOURCE},
    )

    # When
    response = admin_client_new.get(_url(environment))

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "failure_event": None,
        "success_event": None,
        "events_stored_in_flagsmith": True,
    }


def test_signal_source_view__put_then_delete__saves_and_removes_the_source(
    admin_client_new: APIClient,
    environment: Environment,
) -> None:
    # Given
    body = {"failure_event": "checkout_failed", "success_event": "checkout_completed"}

    # When
    saved = admin_client_new.put(_url(environment), body, format="json")
    deleted = admin_client_new.delete(_url(environment))

    # Then
    assert saved.status_code == status.HTTP_200_OK
    assert saved.json() == {**body, "events_stored_in_flagsmith": False}
    assert deleted.status_code == status.HTTP_204_NO_CONTENT
    assert not SignalSource.objects.filter(environment=environment).exists()


@pytest.mark.parametrize(
    "body, field",
    [
        ({"failure_event": "$flag_exposure", "success_event": "ok"}, "failure_event"),
        ({"failure_event": "same", "success_event": "same"}, "success_event"),
        ({"failure_event": "", "success_event": "ok"}, "failure_event"),
    ],
)
def test_signal_source_view__invalid_events__returns_400(
    admin_client_new: APIClient,
    environment: Environment,
    body: dict[str, str],
    field: str,
) -> None:
    # Given / When
    response = admin_client_new.put(_url(environment), body, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.json()


def test_signal_source_view__not_an_environment_admin__returns_403(
    staff_client: APIClient,
    environment: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([VIEW_ENVIRONMENT], environment.id, False)

    # When
    response = staff_client.get(_url(environment))

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
