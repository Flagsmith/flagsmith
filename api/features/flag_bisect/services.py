"""Flag Bisect: find which recent flag change caused a regression.

Seven single-purpose agents share the incident as their blackboard; each step is
recorded as an `AgentMessage`:

- Sentinel: watches the failure rate apps report and opens an incident.
- Archivist: reads the environment-default changes around the onset from
  Flagsmith's own history (feature versions in v2, history rows in v1).
- Profiler: turns timing and blast radius into prior odds.
- Guardian: holds the approved envelope and removes the canary at the end.
- Prober: reverts a subset of changes for a canary segment (a system segment with
  a PERCENTAGE_SPLIT condition) through the same service the flag API uses.
- Judge: decides each probe with an always-valid sequential test.
- Scribe: drafts the remediation.

People decide twice: an environment admin approves the envelope before anything
is changed, and restoring the culprit for everyone needs a proposer and a
different approver.
"""

import typing
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import structlog
from django.apps import apps
from django.db import transaction
from django.db.models import F, Max
from django.utils import timezone
from flag_engine.segments.constants import ALL_RULE, PERCENTAGE_SPLIT
from flag_engine.utils.hashing import get_hashed_percentage_for_object_ids
from rest_framework.exceptions import PermissionDenied, ValidationError

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.dataclasses import AuthorData
from core.exceptions import ChangeRequestsEnabledError
from environments.models import Environment
from experimentation.models import (
    Experiment,
    ExperimentStatus,
    SDKExperimentationEvent,
)
from experimentation.warehouses.postgres import is_flagsmith_database_config
from features.feature_segments.services import get_next_segment_override_priority
from features.flag_bisect import engine, metrics
from features.flag_bisect.models import (
    TERMINAL_STATES,
    AgentMessage,
    Incident,
    IncidentState,
    Probe,
    SignalBucket,
    SignalSource,
    Suspect,
)
from features.future.services import delete_segment_override, get_flag, update_flag
from features.future.types import FlagValue, SegmentOverrideRequest
from features.models import Feature
from segments.models import Segment, SegmentManagedBy
from segments.services import delete_segment, write_segment_rules

logger = structlog.get_logger("flag_bisect")

RawValue = str | int | bool | None

BUCKET = timedelta(minutes=1)
LOOKBACK = timedelta(minutes=45)
SUSPECT_WINDOW = timedelta(hours=2)
# Traffic right after a segment change may still carry cached flags.
SETTLE = timedelta(seconds=30)
PROBE_TIMEOUT = timedelta(minutes=12)
MIN_BUCKETS = 8
MAX_SIGNALS_PER_REQUEST = 1000
MAX_EVENTS_PER_PASS = 20_000

Agent = AgentMessage.Agent


@dataclass(frozen=True)
class Signal:
    identifier: str
    ok: bool


@dataclass(frozen=True)
class FlagChange:
    feature: Feature
    before_enabled: bool
    before_value: RawValue
    after_enabled: bool
    after_value: RawValue
    changed_at: datetime


def _ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _say(incident: Incident, agent: str, text: str) -> None:
    AgentMessage.objects.create(incident=incident, agent=agent, text=text)


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _raw_value(flag_value: FlagValue | None) -> RawValue:
    if flag_value is None:
        return None
    raw = flag_value["value"]
    if flag_value["type"] == "integer":
        return int(raw)
    if flag_value["type"] == "boolean":
        return raw.lower() == "true"
    return raw


def _flag_value(raw: RawValue) -> FlagValue | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return {"type": "boolean", "value": str(raw).lower()}
    if isinstance(raw, int):
        return {"type": "integer", "value": str(raw)}
    return {"type": "string", "value": raw}


def _describe(enabled: bool, value: RawValue) -> str:
    if not enabled:
        return "off"
    return "on" if value in (None, "") else f"on ({value})"


def _author_of(incident: Incident) -> AuthorData:
    return AuthorData(
        user=incident.envelope_approved_by,
        api_key=incident.envelope_approved_by_api_key,
    )


def _audit(incident: Incident, author: AuthorData, log: str) -> None:
    AuditLog.objects.create(
        environment=incident.environment,
        project=incident.environment.project,
        author=author.user,
        master_api_key=author.api_key,
        related_object_id=incident.id,
        related_object_type=RelatedObjectType.FLAG_BISECT.name,
        log=log,
    )


def _same_actor(
    user_a: typing.Any, key_a: typing.Any, user_b: typing.Any, key_b: typing.Any
) -> bool:
    if user_a is not None and user_b is not None:
        return bool(user_a.pk == user_b.pk)
    if key_a is not None and key_b is not None:
        return bool(key_a.pk == key_b.pk)
    return False


# --------------------------------------------------------------------- signals


def canary_key(environment: Environment, identifier: str) -> str:
    """The identity key Flagsmith hashes for percentage splits."""
    if environment.use_identity_composite_key_for_hashing:
        return f"{environment.api_key}_{identifier}"
    identity_model = apps.get_model("identities", "Identity")
    identity_id = (
        identity_model.objects.filter(environment=environment, identifier=identifier)
        .values_list("id", flat=True)
        .first()
    )
    return str(identity_id) if identity_id is not None else identifier


def in_canary(
    environment: Environment, segment_id: int, percent: int, identifier: str
) -> bool:
    """Whether Flagsmith serves this identity the canary segment's overrides.

    Same hash and comparison as flag_engine's PERCENTAGE_SPLIT condition.
    """
    key = canary_key(environment, identifier)
    return get_hashed_percentage_for_object_ids([str(segment_id), key]) <= float(
        percent
    )


def record_signals(
    environment: Environment, signals: list[Signal], at: datetime | None = None
) -> int:
    """Counts outcomes per minute and, during a probe, per cohort.

    `at` dates outcomes read after the fact; it defaults to now.
    """
    if not signals:
        return 0
    now = at or timezone.now()
    minute = now.replace(second=0, microsecond=0)
    failures = sum(not s.ok for s in signals)
    with transaction.atomic():
        bucket, _ = SignalBucket.objects.get_or_create(
            environment=environment, minute=minute
        )
        SignalBucket.objects.filter(pk=bucket.pk).update(
            total=F("total") + len(signals), failures=F("failures") + failures
        )
        probe = (
            Probe.objects.filter(
                incident__environment=environment,
                ended_at__isnull=True,
                settles_at__lte=now,
                incident__canary_segment__isnull=False,
            )
            .select_related("incident")
            .first()
        )
        if probe is not None:
            incident = probe.incident
            segment_id = typing.cast(int, incident.canary_segment_id)
            canary = [
                s
                for s in signals
                if in_canary(
                    environment, segment_id, incident.canary_percent, s.identifier
                )
            ]
            canary_failures = sum(not s.ok for s in canary)
            Probe.objects.filter(pk=probe.pk).update(
                canary_total=F("canary_total") + len(canary),
                canary_failures=F("canary_failures") + canary_failures,
                main_total=F("main_total") + len(signals) - len(canary),
                main_failures=F("main_failures") + failures - canary_failures,
            )
    metrics.flagsmith_flag_bisect_signals_total.labels(outcome="ok").inc(
        len(signals) - failures
    )
    metrics.flagsmith_flag_bisect_signals_total.labels(outcome="failed").inc(failures)
    return len(signals)


def stores_events_in_flagsmith(environment: Environment) -> bool:
    """Whether the environment's apps send Experimentation events to this Flagsmith."""
    config = environment.warehouse_connections.values_list("config", flat=True).first()
    return is_flagsmith_database_config(config)


def describe_signal_source(environment: Environment) -> dict[str, typing.Any]:
    source = SignalSource.objects.filter(environment=environment).first()
    return {
        "failure_event": source.failure_event if source else None,
        "success_event": source.success_event if source else None,
        "events_stored_in_flagsmith": stores_events_in_flagsmith(environment),
    }


def set_signal_source(
    environment: Environment, failure_event: str, success_event: str
) -> SignalSource:
    """Saves which Experimentation events count as outcomes.

    A new source reads back no further than the look-back window.
    """
    source = SignalSource.objects.filter(environment=environment).first()
    if source is None:
        older = SDKExperimentationEvent.objects.filter(
            environment_key=environment.api_key,
            timestamp__lt=timezone.now() - LOOKBACK,
        ).aggregate(last=Max("id"))["last"]
        source = SignalSource(environment=environment, last_event_id=older or 0)
    source.failure_event = failure_event
    source.success_event = success_event
    source.save()
    logger.info(
        "signal_source.saved",
        organisation__id=environment.project.organisation_id,
        environment__id=environment.id,
    )
    return source


def ingest_experimentation_events(
    source: SignalSource, now: datetime | None = None
) -> int:
    """Counts the source's Experimentation events, oldest unread first.

    Events are dated by when they happened, one minute at a time, so a minute
    that straddles a probe's settling time counts towards neither cohort.
    """
    now = now or timezone.now()
    environment = source.environment
    rows = list(
        SDKExperimentationEvent.objects.filter(
            environment_key=environment.api_key,
            event__in=(source.failure_event, source.success_event),
            id__gt=source.last_event_id,
        )
        .order_by("id")
        .values_list("id", "event", "identifier", "timestamp")[:MAX_EVENTS_PER_PASS]
    )
    if not rows:
        return 0
    by_minute: dict[datetime, list[tuple[datetime, Signal]]] = {}
    for _, event, identifier, timestamp in rows:
        if not identifier or timestamp < now - LOOKBACK:
            continue
        # An SDK clock running ahead would otherwise lose the event for good.
        timestamp = min(timestamp, now)
        signal = Signal(identifier, event == source.success_event)
        minute = timestamp.replace(second=0, microsecond=0)
        by_minute.setdefault(minute, []).append((timestamp, signal))
    counted = 0
    for minute in sorted(by_minute):
        group = by_minute[minute]
        counted += record_signals(
            environment, [s for _, s in group], at=min(t for t, _ in group)
        )
    source.last_event_id = rows[-1][0]
    source.save(update_fields=["last_event_id", "updated_at"])
    return counted


def _buckets(
    environment: Environment, since: datetime, until: datetime
) -> list[engine.Bucket]:
    rows = SignalBucket.objects.filter(
        environment=environment, minute__gte=since, minute__lt=until
    ).order_by("minute")
    return [engine.Bucket(_ms(r.minute), r.total, r.failures) for r in rows]


# --------------------------------------------------------------------- archivist


def _typed_history_value(row: typing.Any) -> RawValue:
    value_type = row.type
    if value_type == "int":
        return typing.cast(int | None, row.integer_value)
    if value_type == "bool":
        return typing.cast(bool | None, row.boolean_value)
    return typing.cast(str | None, row.string_value)


def _v1_changes(
    environment: Environment, since: datetime, until: datetime
) -> dict[int, dict[str, typing.Any]]:
    """Latest enabled and value change per feature, from simple-history rows."""
    feature_state_model = apps.get_model("features", "FeatureState")
    history_fs = apps.get_model("features", "HistoricalFeatureState")
    history_fsv = apps.get_model("features", "HistoricalFeatureStateValue")
    defaults = dict(
        feature_state_model.objects.filter(
            environment=environment,
            identity__isnull=True,
            feature_segment__isnull=True,
        ).values_list("id", "feature_id")
    )
    found: dict[int, dict[str, typing.Any]] = {}

    def previous(model: typing.Any, row: typing.Any, field: str) -> typing.Any:
        return (
            model.objects.filter(**{field: getattr(row, field)})
            .filter(history_id__lt=row.history_id)
            .order_by("-history_id")
            .first()
        )

    for row in history_fs.objects.filter(
        id__in=defaults,
        history_type="~",
        history_date__gte=since,
        history_date__lte=until,
    ).order_by("history_date", "history_id"):
        prior = previous(history_fs, row, "id")
        if prior is not None and prior.enabled != row.enabled:
            entry = found.setdefault(defaults[row.id], {})
            entry["enabled"] = (prior.enabled, row.history_date)
    for row in history_fsv.objects.filter(
        feature_state_id__in=defaults,
        history_type="~",
        history_date__gte=since,
        history_date__lte=until,
    ).order_by("history_date", "history_id"):
        prior = previous(history_fsv, row, "feature_state_id")
        if prior is not None and _typed_history_value(prior) != _typed_history_value(
            row
        ):
            entry = found.setdefault(defaults[row.feature_state_id], {})
            entry["value"] = (_typed_history_value(prior), row.history_date)
    return found


def _v2_changes(
    environment: Environment, since: datetime, until: datetime
) -> dict[int, dict[str, typing.Any]]:
    """Latest enabled and value change per feature, from published feature versions."""
    version_model = apps.get_model("feature_versioning", "EnvironmentFeatureVersion")
    found: dict[int, dict[str, typing.Any]] = {}

    def default_state(version: typing.Any) -> typing.Any:
        return version.feature_states.filter(
            feature_segment__isnull=True, identity__isnull=True
        ).first()

    versions = version_model.objects.filter(
        environment=environment,
        published_at__isnull=False,
        live_from__gte=since,
        live_from__lte=min(until, timezone.now()),
    ).order_by("live_from")
    for version in versions:
        previous_version = version.get_previous_version()
        after, before = (
            default_state(version),
            (default_state(previous_version) if previous_version else None),
        )
        if after is None or before is None:
            continue
        entry = found.setdefault(version.feature_id, {})
        if before.enabled != after.enabled:
            entry["enabled"] = (before.enabled, version.live_from)
        if before.get_feature_state_value() != after.get_feature_state_value():
            entry["value"] = (before.get_feature_state_value(), version.live_from)
    return found


def recent_changes(
    environment: Environment, since: datetime, until: datetime
) -> list[FlagChange]:
    """Environment-default changes in [since, until], one per feature.

    `before` is the state just before the feature's latest change (what a revert
    restores); `after` is what Flagsmith serves now.
    """
    reader = _v2_changes if environment.use_v2_feature_versioning else _v1_changes
    found = reader(environment, since, until)
    changes: list[FlagChange] = []
    for feature in Feature.objects.filter(id__in=found.keys()):
        entry = found[feature.id]
        current = get_flag(environment=environment, feature=feature)[
            "environment_default"
        ]
        after_enabled, after_value = current["enabled"], _raw_value(current["value"])
        enabled_change = entry.get("enabled")
        value_change = entry.get("value")
        before_enabled = enabled_change[0] if enabled_change else after_enabled
        before_value = value_change[0] if value_change else after_value
        if (before_enabled, before_value) == (after_enabled, after_value):
            continue  # changed and changed back
        changed_at = max(c[1] for c in (enabled_change, value_change) if c is not None)
        changes.append(
            FlagChange(
                feature,
                before_enabled,
                before_value,
                after_enabled,
                after_value,
                changed_at,
            )
        )
    return sorted(changes, key=lambda c: (c.changed_at, c.feature.id))


# --------------------------------------------------------------------- beliefs


def _load_beliefs(incident: Incident) -> list[engine.Belief]:
    return [
        engine.Belief(engine.Hypothesis(tuple(ids)), float(p))
        for ids, p in incident.beliefs
    ]


def _store_beliefs(incident: Incident, beliefs: list[engine.Belief]) -> None:
    incident.beliefs = [[list(b.hypothesis.ids), b.p] for b in beliefs]


def posteriors(incident: Incident) -> dict[str, float]:
    return engine.involvement(_load_beliefs(incident))


def hypotheses(incident: Incident, limit: int = 8) -> list[tuple[list[str], float]]:
    beliefs = sorted(_load_beliefs(incident), key=lambda b: (-b.p, b.hypothesis.key))
    return [(list(b.hypothesis.ids), b.p) for b in beliefs[:limit]]


# --------------------------------------------------------------------- sentinel


def _open_incident(environment: Environment) -> Incident | None:
    return (
        Incident.objects.filter(environment=environment)
        .exclude(state__in=TERMINAL_STATES)
        .first()
    )


def watch_environment(
    environment: Environment, now: datetime | None = None
) -> Incident | None:
    """Sentinel. Opens an incident when the failure rate shifts; confirms recovery."""
    now = now or timezone.now()
    current = _open_incident(environment)
    if current is not None:
        if current.state == IncidentState.REMEDIATED:
            _check_recovery(current, now)
        return None
    latest = Incident.objects.filter(environment=environment).first()
    since = now - LOOKBACK
    if latest is not None and latest.updated_at > since:
        since = latest.updated_at
    buckets = _buckets(environment, since, now.replace(second=0, microsecond=0))
    if len(buckets) < MIN_BUCKETS:
        return None
    onset = engine.detect_onset(buckets)
    if not onset.alarmed or onset.onset_at is None:
        return None
    after = [b for b in buckets if b.start >= onset.onset_at]
    if len(after) < 2:
        return None  # confirm on two complete minutes first
    regression_rate = sum(b.failures for b in after) / max(1, sum(b.n for b in after))
    onset_at = datetime.fromtimestamp(onset.onset_at / 1000, tz=UTC)
    incident = Incident.objects.create(
        environment=environment,
        state=IncidentState.INVESTIGATING,
        onset_at=onset_at,
        baseline_rate=onset.baseline_rate,
        regression_rate=regression_rate,
    )
    metrics.flagsmith_flag_bisect_incidents_total.inc()
    logger.info(
        "incident.opened",
        organisation__id=environment.project.organisation_id,
        environment__id=environment.id,
        incident__id=incident.id,
    )
    _say(
        incident,
        Agent.SENTINEL,
        f"Failure rate rose from {_pct(onset.baseline_rate)} to {_pct(regression_rate)}. "
        f"Onset at {onset_at:%H:%M} UTC.",
    )
    _investigate(incident, now)
    return incident


def _advise_canary(incident: Incident, now: datetime) -> engine.CanaryAdvice:
    """Sizes the canary from the traffic since the onset and the size of the regression."""
    since = incident.onset_at.replace(second=0, microsecond=0)
    minutes = _buckets(
        incident.environment, since, now.replace(second=0, microsecond=0)
    )
    per_minute = sum(b.n for b in minutes) / max(1, len(minutes))
    return engine.recommend_canary(
        per_minute, incident.baseline_rate, incident.regression_rate
    )


def _in_experiments(
    environment: Environment, changes: list[FlagChange]
) -> list[FlagChange]:
    """Changes to flags whose rollout an experiment controls; the swarm never overrides those."""
    feature_ids = set(
        Experiment.objects.filter(
            environment=environment,
            feature_id__in=[c.feature.id for c in changes],
            status__in=(ExperimentStatus.RUNNING, ExperimentStatus.PAUSED),
        ).values_list("feature_id", flat=True)
    )
    return [c for c in changes if c.feature.id in feature_ids]


def _investigate(incident: Incident, now: datetime) -> None:
    """Archivist, Profiler and Guardian: suspects, priors and the proposed envelope."""
    changes = recent_changes(
        incident.environment, incident.onset_at - SUSPECT_WINDOW, now
    )
    experimented = _in_experiments(incident.environment, changes)
    if experimented:
        _say(
            incident,
            Agent.ARCHIVIST,
            "Left alone because an experiment is running on them: "
            + ", ".join(c.feature.name for c in experimented)
            + ". Pause or complete the experiment to include them.",
        )
        changes = [c for c in changes if c not in experimented]
    if not changes:
        _say(
            incident,
            Agent.ARCHIVIST,
            "No flag changes in the 2 hours before the onset.",
        )
        _finish(incident, IncidentState.NOT_A_FLAG_CHANGE, "not_a_flag_change")
        return
    _say(
        incident,
        Agent.ARCHIVIST,
        f"Found {len(changes)} flag change(s): "
        + ", ".join(c.feature.name for c in changes)
        + ".",
    )
    # Dated to its minute; a change inside that minute can still be the cause.
    reference = _ms(incident.onset_at + BUCKET)
    beliefs = engine.priors(
        [engine.Change(str(c.feature.id), _ms(c.changed_at)) for c in changes],
        reference,
    )
    prior = engine.involvement(beliefs)
    for change in changes:
        Suspect.objects.create(
            incident=incident,
            feature=change.feature,
            before_enabled=change.before_enabled,
            before_value=change.before_value,
            after_enabled=change.after_enabled,
            after_value=change.after_value,
            changed_at=change.changed_at,
            prior=prior.get(str(change.feature.id), 0.0),
        )
    _store_beliefs(incident, beliefs)
    top = sorted(changes, key=lambda c: -prior.get(str(c.feature.id), 0.0))[:3]
    _say(
        incident,
        Agent.PROFILER,
        "Prior odds favour "
        + ", ".join(
            f"{c.feature.name} ({prior[str(c.feature.id)] * 100:.0f}%)" for c in top
        )
        + ".",
    )
    advice = _advise_canary(incident, now)
    incident.canary_percent = advice.percent
    incident.state = IncidentState.AWAITING_APPROVAL
    incident.save()
    if advice.minutes is None:
        pace = (
            " At your current traffic even this canary may not decide a probe in time;"
            " expect an inconclusive result unless traffic rises."
        )
    else:
        pace = f" At your current traffic, each probe should take about {advice.minutes:g} minutes."
    _say(
        incident,
        Agent.GUARDIAN,
        f"Proposed envelope: revert any of {len(changes)} change(s) for "
        f"{incident.canary_percent}% of identities only, at most {incident.max_rounds} rounds "
        f"and {incident.max_minutes} minutes.{pace} "
        "Nothing changes until an environment admin approves.",
    )


def _check_recovery(incident: Incident, now: datetime) -> None:
    """Resolved once complete minutes after the fix are close to the baseline again.

    Minutes that began before the fix still hold failing traffic, so they never count.
    """
    remediated_at = incident.remediated_at or incident.updated_at
    first = remediated_at.replace(second=0, microsecond=0) + BUCKET
    until = now.replace(second=0, microsecond=0)
    recent = _buckets(incident.environment, max(first, until - 3 * BUCKET), until)
    total = sum(b.n for b in recent)
    failures = sum(b.failures for b in recent)
    threshold = (
        incident.baseline_rate + (incident.regression_rate - incident.baseline_rate) / 3
    )
    if total >= 300 and failures / total <= threshold:
        _say(
            incident,
            Agent.SENTINEL,
            f"Failure rate is back to {_pct(failures / total)} "
            f"(baseline {_pct(incident.baseline_rate)}).",
        )
        incident.state = IncidentState.RESOLVED
        incident.save()
        logger.info(
            "incident.resolved",
            environment__id=incident.environment_id,
            incident__id=incident.id,
        )


# --------------------------------------------------------------------- gate 1


def _require_no_change_requests(environment: Environment) -> None:
    if environment.is_workflow_enabled:
        raise ChangeRequestsEnabledError()


def approve_envelope(
    incident: Incident,
    author: AuthorData,
    canary_percent: int | None = None,
    max_rounds: int | None = None,
    max_minutes: int | None = None,
) -> Incident:
    """Gate 1. Creates the canary segment; nothing else changes yet."""
    with transaction.atomic():
        incident = Incident.objects.select_for_update().get(pk=incident.pk)
        if incident.state != IncidentState.AWAITING_APPROVAL:
            raise ValidationError(
                f"The incident is {incident.state}, not awaiting approval."
            )
        _require_no_change_requests(incident.environment)
        if canary_percent is not None:
            incident.canary_percent = canary_percent
        if max_rounds is not None:
            incident.max_rounds = max_rounds
        if max_minutes is not None:
            incident.max_minutes = max_minutes
        rules: typing.Any = [
            {
                "type": ALL_RULE,
                "conditions": [
                    {
                        "property": "$.identity.key",
                        "operator": PERCENTAGE_SPLIT,
                        "value": str(incident.canary_percent),
                        "description": None,
                    }
                ],
                "rules": [],
            }
        ]
        segment = Segment.objects.create(
            name=f"flag-bisect-{incident.id}-canary",
            project=incident.environment.project,
            is_system_segment=True,
            managed_by=SegmentManagedBy.FLAG_BISECT,
            rules_data=rules,
        )
        write_segment_rules(segment, rules)
        incident.canary_segment = segment
        incident.envelope_approved_by = author.user
        incident.envelope_approved_by_api_key = author.api_key
        incident.envelope_approved_at = timezone.now()
        incident.state = IncidentState.PROBING
        incident.save()
        _say(
            incident,
            Agent.HUMAN,
            f"Envelope approved: {incident.canary_percent}% canary, {incident.max_rounds} rounds, "
            f"{incident.max_minutes} minutes.",
        )
        _audit(
            incident, author, f"Flag Bisect incident #{incident.id}: envelope approved"
        )
    logger.info(
        "envelope.approved",
        environment__id=incident.environment_id,
        incident__id=incident.id,
    )
    return incident


def abort(incident: Incident, author: AuthorData, reason: str) -> Incident:
    if incident.state in TERMINAL_STATES or incident.state == IncidentState.REMEDIATED:
        raise ValidationError(f"The incident is {incident.state}.")
    _teardown(incident)
    _say(incident, Agent.HUMAN, f"Stopped: {reason}")
    _audit(incident, author, f"Flag Bisect incident #{incident.id}: stopped")
    _finish(incident, IncidentState.ABORTED, "aborted")
    return incident


# --------------------------------------------------------------------- prober and judge


def _apply(incident: Incident, suspects: list[Suspect]) -> None:
    """Reverts each suspect's on/off state and value for the canary only.

    The canary keeps the environment's current variant split, so a multivariate
    flag serves the canary the same mix of variants as everyone else.
    """
    author = _author_of(incident)
    segment_id = typing.cast(int, incident.canary_segment_id)
    for suspect in suspects:
        override: SegmentOverrideRequest = {
            "segment": {"id": segment_id},
            "enabled": suspect.before_enabled,
            "value": _flag_value(suspect.before_value),
            "priority": get_next_segment_override_priority(
                environment=incident.environment, feature=suspect.feature
            ),
        }
        split = get_flag(environment=incident.environment, feature=suspect.feature)[
            "environment_default"
        ]["variants"]
        if split:  # Only multivariate flags accept variants.
            override["variants"] = split
        update_flag(
            environment=incident.environment,
            feature=suspect.feature,
            changes={"segment_overrides": [override]},
            replace=False,
            author=author,
            overwrite_system_segment_overrides=True,
        )


def _clear(incident: Incident, suspects: typing.Iterable[Suspect]) -> None:
    author = _author_of(incident)
    for suspect in suspects:
        try:
            delete_segment_override(
                environment=incident.environment,
                feature=suspect.feature,
                segment_id=typing.cast(int, incident.canary_segment_id),
                author=author,
                overwrite_system_segment_overrides=True,
            )
        except Exception as error:  # noqa: BLE001 - already removed is fine
            logger.info(
                "override.already_removed",
                incident__id=incident.id,
                feature__id=suspect.feature_id,
                error=type(error).__name__,
            )


def _teardown(incident: Incident) -> None:
    """Guardian: remove any probe overrides, then the canary segment."""
    open_probe = incident.probes.filter(ended_at__isnull=True).first()
    if open_probe is not None:
        _clear(incident, open_probe.reverted.all())
        open_probe.ended_at = timezone.now()
        open_probe.save()
    if incident.canary_segment is not None:
        delete_segment(incident.canary_segment, _author_of(incident))
        incident.canary_segment = None
        incident.save()


def _finish(incident: Incident, state: str, result: str) -> None:
    incident.state = state
    incident.save()
    metrics.flagsmith_flag_bisect_conclusions_total.labels(result=result).inc()
    logger.info(
        "incident.concluded",
        environment__id=incident.environment_id,
        incident__id=incident.id,
        result=result,
    )


def step(incident: Incident, now: datetime | None = None) -> None:
    """One swarm step for an incident that is probing or confirming."""
    now = now or timezone.now()
    if incident.state not in (IncidentState.PROBING, IncidentState.CONFIRMING):
        return
    open_probe = incident.probes.filter(ended_at__isnull=True).first()
    if open_probe is None:
        _start_probe(incident, now)
    elif now >= open_probe.settles_at:
        _judge_probe(incident, open_probe, now)


def _start_probe(incident: Incident, now: datetime) -> None:
    approved_at = typing.cast(datetime, incident.envelope_approved_at)
    if incident.rounds >= incident.max_rounds or now - approved_at > timedelta(
        minutes=incident.max_minutes
    ):
        _teardown(incident)
        _say(
            incident,
            Agent.GUARDIAN,
            f"Envelope exhausted after {incident.rounds} round(s); canary removed.",
        )
        _finish(incident, IncidentState.INCONCLUSIVE, "inconclusive")
        return
    suspects = {s.key: s for s in incident.suspects.all()}
    kind = Probe.Kind.BISECT
    if incident.state == IncidentState.CONFIRMING and incident.conclusion:
        keys = list(incident.conclusion["ids"])
        kind = Probe.Kind.CONFIRM
    else:
        design = engine.design_probe(_load_beliefs(incident), list(suspects))
        if design is None:
            incident.rounds = incident.max_rounds
            incident.save()
            return
        keys = list(design.revert)
    reverted = [suspects[k] for k in keys]
    _apply(incident, reverted)
    incident.rounds += 1
    incident.save()
    probe = Probe.objects.create(
        incident=incident,
        round=incident.rounds,
        kind=kind,
        started_at=now,
        settles_at=now + SETTLE,
    )
    probe.reverted.set(reverted)
    _say(
        incident,
        Agent.PROBER,
        f"Round {probe.round}{' (confirmation)' if kind == Probe.Kind.CONFIRM else ''}: "
        f"reverting {', '.join(s.feature.name for s in reverted)} for the canary only.",
    )
    _audit(
        incident,
        _author_of(incident),
        f"Flag Bisect incident #{incident.id} round {probe.round}: canary reverts "
        + ", ".join(s.feature.name for s in reverted),
    )
    logger.info(
        "probe.started",
        environment__id=incident.environment_id,
        incident__id=incident.id,
        probe__round=probe.round,
    )


def _judge_probe(incident: Incident, probe: Probe, now: datetime) -> None:
    judgement = engine.judge(
        engine.Cohort(probe.canary_total, probe.canary_failures),
        engine.Cohort(probe.main_total, probe.main_failures),
        incident.baseline_rate,
    )
    timed_out = now - probe.started_at > PROBE_TIMEOUT
    if judgement.verdict == "inconclusive" and not timed_out:
        return
    reverted = list(probe.reverted.all())
    probe.verdict = judgement.verdict
    probe.judgement = {
        "canary_rate": judgement.canary_rate,
        "main_rate": judgement.main_rate,
        "recovered": judgement.recovered,
        "evidence": min(judgement.evidence, 1e12),
        "reason": judgement.reason,
    }
    probe.ended_at = now
    probe.save()
    metrics.flagsmith_flag_bisect_probes_total.labels(verdict=judgement.verdict).inc()
    _say(
        incident,
        Agent.JUDGE,
        f"Round {probe.round}: {judgement.verdict.replace('_', ' ')}; {judgement.reason}.",
    )
    if judgement.verdict == "harmful":
        _teardown(incident)
        _say(incident, Agent.GUARDIAN, "Aborted: the canary got worse. Canary removed.")
        _finish(incident, IncidentState.ABORTED, "aborted")
        return
    _clear(incident, reverted)
    keys = [s.key for s in reverted]
    if probe.kind == Probe.Kind.CONFIRM:
        if judgement.verdict == "healed":
            incident.confirmed = True
            _teardown(incident)
            _draft_remediation(incident)
            incident.state = IncidentState.IDENTIFIED
            incident.save()
            return
        incident.conclusion = None
        incident.state = IncidentState.PROBING
    beliefs = engine.update(_load_beliefs(incident), keys, judgement.verdict)
    _store_beliefs(incident, beliefs)
    incident.save()
    if probe.kind == Probe.Kind.CONFIRM:
        return
    conclusion = engine.conclude(beliefs)
    if conclusion.status == "identified":
        incident.conclusion = {
            "ids": list(conclusion.top.ids),
            "confidence": conclusion.confidence,
        }
        incident.state = IncidentState.CONFIRMING
        incident.save()
        _say(
            incident,
            Agent.JUDGE,
            f"{conclusion.confidence * 100:.1f}% on one explanation; confirming before anyone acts.",
        )
    elif conclusion.status == "not_a_flag_change":
        _teardown(incident)
        incident.conclusion = {"ids": [], "confidence": conclusion.confidence}
        _say(
            incident, Agent.SCRIBE, "None of these flag changes caused the regression."
        )
        _finish(incident, IncidentState.NOT_A_FLAG_CHANGE, "not_a_flag_change")


def _culprits(incident: Incident) -> list[Suspect]:
    ids = set((incident.conclusion or {}).get("ids", []))
    return [s for s in incident.suspects.all() if s.key in ids]


def _draft_remediation(incident: Incident) -> None:
    culprits = _culprits(incident)
    _say(
        incident,
        Agent.SCRIBE,
        "Confirmed: "
        + " + ".join(s.feature.name for s in culprits)
        + ". Draft: restore "
        + ", ".join(
            f"{s.feature.name} to {_describe(s.before_enabled, s.before_value)}"
            for s in culprits
        )
        + " for everyone. One person proposes, a different person approves.",
    )
    metrics.flagsmith_flag_bisect_conclusions_total.labels(result="identified").inc()
    logger.info(
        "incident.concluded",
        environment__id=incident.environment_id,
        incident__id=incident.id,
        result="identified",
    )


# --------------------------------------------------------------------- gate 2


def propose_remediation(incident: Incident, author: AuthorData) -> Incident:
    if incident.state != IncidentState.IDENTIFIED:
        raise ValidationError(
            "A remediation can be proposed once a culprit is confirmed."
        )
    incident.remediation_proposed_by = author.user
    incident.remediation_proposed_by_api_key = author.api_key
    incident.state = IncidentState.REMEDIATION_PROPOSED
    incident.save()
    _say(
        incident,
        Agent.HUMAN,
        "Remediation proposed; it needs a different person to approve.",
    )
    _audit(
        incident, author, f"Flag Bisect incident #{incident.id}: remediation proposed"
    )
    return incident


def approve_remediation(incident: Incident, author: AuthorData) -> Incident:
    """Gate 2. Restores the culprit for everyone, then reads it back."""
    if incident.state != IncidentState.REMEDIATION_PROPOSED:
        raise ValidationError("There is no proposed remediation to approve.")
    if _same_actor(
        incident.remediation_proposed_by,
        incident.remediation_proposed_by_api_key,
        author.user,
        author.api_key,
    ):
        raise PermissionDenied(
            "The remediation needs a second person: the proposer cannot approve it."
        )
    _require_no_change_requests(incident.environment)
    restored: list[dict[str, typing.Any]] = []
    for suspect in _culprits(incident):
        update_flag(
            environment=incident.environment,
            feature=suspect.feature,
            changes={
                "environment_default": {
                    "enabled": suspect.before_enabled,
                    "value": _flag_value(suspect.before_value),
                }
            },
            replace=False,
            author=author,
            overwrite_system_segment_overrides=False,
        )
        current = get_flag(environment=incident.environment, feature=suspect.feature)[
            "environment_default"
        ]
        read_back = (current["enabled"], _raw_value(current["value"]))
        restored.append(
            {
                "feature": suspect.feature.name,
                "verified": read_back == (suspect.before_enabled, suspect.before_value),
            }
        )
    incident.remediation_approved_by = author.user
    incident.remediation_approved_by_api_key = author.api_key
    incident.remediation_result = {"restored": restored}
    incident.remediated_at = timezone.now()
    incident.state = IncidentState.REMEDIATED
    incident.save()
    _say(
        incident,
        Agent.PROBER,
        "Restored "
        + ", ".join(r["feature"] for r in restored)
        + (
            " and read back."
            if all(r["verified"] for r in restored)
            else "; the read-back did not match."
        ),
    )
    _audit(
        incident, author, f"Flag Bisect incident #{incident.id}: remediation applied"
    )
    logger.info(
        "remediation.applied",
        environment__id=incident.environment_id,
        incident__id=incident.id,
    )
    return incident


def run_swarm(now: datetime | None = None) -> None:
    """One pass over every environment with recent signals."""
    now = now or timezone.now()
    for source in SignalSource.objects.select_related("environment"):
        ingest_experimentation_events(source, now)
    environment_ids = (
        SignalBucket.objects.filter(minute__gte=now - timedelta(minutes=15))
        .values_list("environment_id", flat=True)
        .distinct()
    )
    for environment in Environment.objects.filter(id__in=list(environment_ids)):
        watch_environment(environment, now)
    for incident in Incident.objects.filter(
        state__in=(IncidentState.PROBING, IncidentState.CONFIRMING)
    ):
        step(incident, now)
