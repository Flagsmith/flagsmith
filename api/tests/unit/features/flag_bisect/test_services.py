import random
import typing
from datetime import timedelta

import pytest
from django.urls import reverse
from freezegun.api import FrozenDateTimeFactory
from pytest_django.fixtures import SettingsWrapper
from pytest_structlog import StructuredLogCapture
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.dataclasses import AuthorData
from core.exceptions import ChangeRequestsEnabledError
from environments.models import Environment
from features.flag_bisect import services
from features.flag_bisect.models import Incident, IncidentState, Probe
from features.future.services import get_flag, update_flag
from features.models import Feature
from projects.models import Project
from segments.models import Segment
from segments.services import write_segment_rules
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db

FEATURES = ["promo_banner", "search_reranker", "fast_checkout", "new_tax_engine"]


@pytest.fixture(autouse=True)
def flag_bisect_enabled(settings: SettingsWrapper) -> None:
    settings.FLAG_BISECT_ENABLED = True


@pytest.fixture(params=["v1", "v2"])
def bisect_environment(
    request: pytest.FixtureRequest, environment: Environment
) -> Environment:
    if request.param == "v2":
        return typing.cast(
            Environment, request.getfixturevalue("environment_v2_versioning")
        )
    return environment


class World:
    """Shoppers whose requests fail while the hidden culprit is served to them."""

    def __init__(
        self,
        environment: Environment,
        features: dict[str, Feature],
        culprit: str | None,
        seed: int = 1,
    ) -> None:
        self.environment = environment
        self.features = features
        self.culprit = culprit
        self.rng = random.Random(seed)

    def serves_culprit(self, identifier: str) -> bool:
        assert self.culprit is not None
        feature = self.features[self.culprit]
        enabled = get_flag(environment=self.environment, feature=feature)[
            "environment_default"
        ]["enabled"]
        probe = Probe.objects.filter(
            incident__environment=self.environment, ended_at__isnull=True
        ).first()
        if probe is not None and probe.reverted.filter(feature=feature).exists():
            incident = probe.incident
            if services.in_canary(
                self.environment,
                typing.cast(int, incident.canary_segment_id),
                incident.canary_percent,
                identifier,
            ):
                return False
        return enabled

    def traffic(self, count: int, broken: bool = True) -> list[services.Signal]:
        identifiers = [f"shopper-{self.rng.randrange(20000)}" for _ in range(count)]
        if self.culprit is None:
            return [
                services.Signal(i, self.rng.random() >= (0.08 if broken else 0.01))
                for i in identifiers
            ]
        enabled = get_flag(
            environment=self.environment, feature=self.features[self.culprit]
        )["environment_default"]["enabled"]
        probe_open = Probe.objects.filter(
            incident__environment=self.environment, ended_at__isnull=True
        ).exists()
        signals = []
        for identifier in identifiers:
            failing = self.serves_culprit(identifier) if probe_open else enabled
            signals.append(
                services.Signal(
                    identifier, self.rng.random() >= (0.08 if failing else 0.01)
                )
            )
        return signals


def _deploy(
    environment: Environment,
    project: Project,
    author: AuthorData,
    freezer: FrozenDateTimeFactory,
) -> dict[str, Feature]:
    features = {
        name: Feature.objects.create(name=name, project=project, default_enabled=False)
        for name in FEATURES
    }
    # In v2, a version published at the exact instant the feature was created finds no
    # previous version to clone (`live_from <` is strict); only a frozen clock does that.
    freezer.tick(timedelta(seconds=1))
    for feature in features.values():
        update_flag(
            environment=environment,
            feature=feature,
            changes={"environment_default": {"enabled": True}},
            replace=False,
            author=author,
            overwrite_system_segment_overrides=False,
        )
        freezer.tick(timedelta(seconds=10))
    return features


def _baseline(environment: Environment, freezer: FrozenDateTimeFactory) -> None:
    rng = random.Random(9)
    for _ in range(10):
        services.record_signals(
            environment,
            [services.Signal(f"warm-{i}", rng.random() >= 0.01) for i in range(400)],
        )
        freezer.tick(timedelta(minutes=1))


def _run_until(
    world: World,
    freezer: FrozenDateTimeFactory,
    done: typing.Callable[[], bool],
    max_steps: int = 400,
    per_step: int = 300,
) -> None:
    for _ in range(max_steps):
        if done():
            return
        services.record_signals(world.environment, world.traffic(per_step))
        services.run_swarm()
        freezer.tick(timedelta(seconds=20))
    raise AssertionError(
        f"not done after {max_steps} steps: {list(Incident.objects.values())}"
    )


def _incident(environment: Environment) -> Incident | None:
    return Incident.objects.filter(environment=environment).first()


def _state(environment: Environment) -> str | None:
    incident = _incident(environment)
    return None if incident is None else incident.state


def test_bisect__single_culprit__is_found_confirmed_and_restored_by_two_people(
    bisect_environment: Environment,
    project: Project,
    admin_user: FFAdminUser,
    staff_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
    log: StructuredLogCapture,
) -> None:
    # Given
    environment = bisect_environment
    freezer.move_to("2026-11-26T10:00:00Z")
    _baseline(environment, freezer)
    alice, bob = AuthorData(user=admin_user), AuthorData(user=staff_user)
    features = _deploy(environment, project, alice, freezer)
    world = World(environment, features, culprit="new_tax_engine")

    # When the regression is detected
    _run_until(
        world, freezer, lambda: _state(environment) == IncidentState.AWAITING_APPROVAL
    )

    # Then nothing changed in Flagsmith before a person approved
    incident = typing.cast(Incident, _incident(environment))
    assert {s.feature.name for s in incident.suspects.all()} == set(FEATURES)
    assert incident.canary_segment is None
    assert incident.regression_rate > 0.05

    # When the envelope is approved and the swarm probes
    services.approve_envelope(incident, alice, canary_percent=10)
    _run_until(world, freezer, lambda: _state(environment) == IncidentState.IDENTIFIED)

    # Then the culprit is confirmed and the canary is gone
    incident.refresh_from_db()
    assert incident.confirmed is True
    assert incident.conclusion is not None
    assert incident.conclusion["ids"] == [str(features["new_tax_engine"].id)]
    assert incident.canary_segment is None
    assert not Segment.objects.filter(name__startswith="flag-bisect-").exists()
    assert incident.probes.last().kind == Probe.Kind.CONFIRM  # type: ignore[union-attr]

    # When one person proposes and the same person tries to approve
    services.propose_remediation(incident, alice)
    with pytest.raises(PermissionDenied):
        services.approve_remediation(incident, alice)

    # And a second person approves
    services.approve_remediation(incident, bob)

    # Then only the culprit is restored, and the incident resolves
    incident.refresh_from_db()
    assert incident.remediation_result == {
        "restored": [{"feature": "new_tax_engine", "verified": True}]
    }
    defaults = {
        name: get_flag(environment=environment, feature=f)["environment_default"][
            "enabled"
        ]
        for name, f in features.items()
    }
    assert defaults == {
        "promo_banner": True,
        "search_reranker": True,
        "fast_checkout": True,
        "new_tax_engine": False,
    }
    _run_until(world, freezer, lambda: _state(environment) == IncidentState.RESOLVED)
    agents = set(incident.messages.values_list("agent", flat=True))
    assert agents >= {
        "sentinel",
        "archivist",
        "profiler",
        "guardian",
        "prober",
        "judge",
        "scribe",
        "human",
    }
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.FLAG_BISECT.name,
            related_object_id=incident.id,
        ).count()
        >= 4
    )
    assert log.has("incident.opened", incident__id=incident.id)
    assert log.has("incident.resolved", incident__id=incident.id)


def test_bisect__regression_from_elsewhere__concludes_not_a_flag_change(
    environment: Environment,
    project: Project,
    admin_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    freezer.move_to("2026-11-26T10:00:00Z")
    _baseline(environment, freezer)
    alice = AuthorData(user=admin_user)
    features = _deploy(environment, project, alice, freezer)
    world = World(environment, features, culprit=None)
    _run_until(
        world, freezer, lambda: _state(environment) == IncidentState.AWAITING_APPROVAL
    )
    incident = typing.cast(Incident, _incident(environment))

    # When (ruling every change out needs more canary traffic than finding one)
    services.approve_envelope(incident, alice, canary_percent=10)
    _run_until(
        world,
        freezer,
        lambda: (
            _state(environment)
            in (IncidentState.NOT_A_FLAG_CHANGE, IncidentState.INCONCLUSIVE)
        ),
        per_step=900,
    )

    # Then
    incident.refresh_from_db()
    assert incident.state == IncidentState.NOT_A_FLAG_CHANGE
    assert incident.canary_segment is None


def test_bisect__no_flag_changes__closes_without_asking_anyone(
    environment: Environment, freezer: FrozenDateTimeFactory
) -> None:
    # Given
    freezer.move_to("2026-11-26T10:00:00Z")
    _baseline(environment, freezer)
    world = World(environment, {}, culprit=None)

    # When
    _run_until(world, freezer, lambda: _state(environment) is not None)

    # Then
    assert _state(environment) == IncidentState.NOT_A_FLAG_CHANGE


def test_watch_environment__too_little_history__does_not_open_an_incident(
    environment: Environment,
) -> None:
    # Given
    services.record_signals(environment, [services.Signal("a", False)] * 10)

    # When
    incident = services.watch_environment(environment)

    # Then
    assert incident is None
    assert services.record_signals(environment, []) == 0


@pytest.fixture()
def awaiting_incident(
    environment: Environment,
    project: Project,
    admin_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
) -> tuple[Incident, World]:
    freezer.move_to("2026-11-26T10:00:00Z")
    _baseline(environment, freezer)
    features = _deploy(environment, project, AuthorData(user=admin_user), freezer)
    world = World(environment, features, culprit="fast_checkout")
    _run_until(
        world, freezer, lambda: _state(environment) == IncidentState.AWAITING_APPROVAL
    )
    return typing.cast(Incident, _incident(environment)), world


def test_approve_envelope__change_requests_enabled__refuses(
    awaiting_incident: tuple[Incident, World], admin_user: FFAdminUser
) -> None:
    # Given
    incident, _ = awaiting_incident
    incident.environment.minimum_change_request_approvals = 1
    incident.environment.save()

    # When / Then
    with pytest.raises(ChangeRequestsEnabledError):
        services.approve_envelope(incident, AuthorData(user=admin_user))


def test_approve_envelope__twice__refuses_the_second(
    awaiting_incident: tuple[Incident, World], admin_user: FFAdminUser
) -> None:
    # Given
    incident, _ = awaiting_incident
    services.approve_envelope(incident, AuthorData(user=admin_user))

    # When / Then
    with pytest.raises(ValidationError):
        services.approve_envelope(incident, AuthorData(user=admin_user))


def test_abort__while_probing__removes_overrides_and_segment(
    awaiting_incident: tuple[Incident, World],
    admin_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    incident, world = awaiting_incident
    services.approve_envelope(incident, AuthorData(user=admin_user))
    services.run_swarm()
    incident.refresh_from_db()
    assert incident.probes.filter(ended_at__isnull=True).exists()

    # When
    services.abort(incident, AuthorData(user=admin_user), "paging the owning team")

    # Then
    incident.refresh_from_db()
    assert incident.state == IncidentState.ABORTED
    assert incident.canary_segment is None
    assert not incident.probes.filter(ended_at__isnull=True).exists()
    for feature in world.features.values():
        assert (
            get_flag(environment=incident.environment, feature=feature)[
                "segment_overrides"
            ]
            == []
        )
    with pytest.raises(ValidationError):
        services.abort(incident, AuthorData(user=admin_user), "again please")


def test_step__envelope_exhausted__ends_inconclusive(
    awaiting_incident: tuple[Incident, World],
    admin_user: FFAdminUser,
    freezer: FrozenDateTimeFactory,
) -> None:
    # Given
    incident, _ = awaiting_incident
    services.approve_envelope(
        incident, AuthorData(user=admin_user), max_rounds=6, max_minutes=5
    )
    freezer.tick(timedelta(minutes=6))
    incident.refresh_from_db()

    # When
    services.step(incident)

    # Then
    incident.refresh_from_db()
    assert incident.state == IncidentState.INCONCLUSIVE
    assert incident.canary_segment is None


def test_propose_and_approve_remediation__wrong_state__refuse(
    awaiting_incident: tuple[Incident, World], admin_user: FFAdminUser
) -> None:
    # Given
    incident, _ = awaiting_incident
    author = AuthorData(user=admin_user)

    # When / Then
    with pytest.raises(ValidationError):
        services.propose_remediation(incident, author)
    with pytest.raises(ValidationError):
        services.approve_remediation(incident, author)


def test_in_canary__sdk_evaluates_the_canary_segment__matches_what_flagsmith_serves(
    environment: Environment,
    project: Project,
    admin_user: FFAdminUser,
    api_client: APIClient,
) -> None:
    # Given a canary segment that reverts one flag for 30% of identities
    feature = Feature.objects.create(
        name="tax_engine", project=project, default_enabled=True
    )
    segment = Segment.objects.create(
        name="canary", project=project, is_system_segment=True
    )
    rules: typing.Any = [
        {
            "type": "ALL",
            "conditions": [
                {
                    "property": "$.identity.key",
                    "operator": "PERCENTAGE_SPLIT",
                    "value": "30",
                    "description": None,
                }
            ],
            "rules": [],
        }
    ]
    segment.rules_data = rules
    segment.save()
    write_segment_rules(segment, rules)
    update_flag(
        environment=environment,
        feature=feature,
        changes={
            "segment_overrides": [{"segment": {"id": segment.id}, "enabled": False}]
        },
        replace=False,
        author=AuthorData(user=admin_user),
        overwrite_system_segment_overrides=True,
    )
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v1:sdk-identities")

    # When
    mismatches = []
    in_canary = 0
    for i in range(120):
        identifier = f"shopper-{i}"
        flags = api_client.get(url, {"identifier": identifier}).json()["flags"]
        served = next(
            f["enabled"] for f in flags if f["feature"]["name"] == "tax_engine"
        )
        predicted = services.in_canary(environment, segment.id, 30, identifier)
        in_canary += predicted
        if served == predicted:  # canary identities are served "off"
            mismatches.append(identifier)

    # Then
    assert mismatches == []
    assert 15 <= in_canary <= 60


def test_canary_key__composite_hashing_off__uses_the_identity_id(
    environment: Environment,
) -> None:
    # Given
    environment.use_identity_composite_key_for_hashing = False
    environment.save()
    from environments.identities.models import Identity

    identity = Identity.objects.create(identifier="known", environment=environment)

    # When / Then
    assert services.canary_key(environment, "known") == str(identity.id)
    assert services.canary_key(environment, "unknown") == "unknown"
