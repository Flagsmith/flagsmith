from django.db import models

from experimentation.constants import MAX_EVENT_NAME_CHARS


class IncidentState(models.TextChoices):
    INVESTIGATING = "INVESTIGATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    PROBING = "PROBING"
    CONFIRMING = "CONFIRMING"
    IDENTIFIED = "IDENTIFIED"
    NOT_A_FLAG_CHANGE = "NOT_A_FLAG_CHANGE"
    INCONCLUSIVE = "INCONCLUSIVE"
    ABORTED = "ABORTED"
    REMEDIATION_PROPOSED = "REMEDIATION_PROPOSED"
    REMEDIATED = "REMEDIATED"
    RESOLVED = "RESOLVED"


TERMINAL_STATES = (
    IncidentState.NOT_A_FLAG_CHANGE,
    IncidentState.INCONCLUSIVE,
    IncidentState.ABORTED,
    IncidentState.RESOLVED,
)


class SignalBucket(models.Model):
    """Outcomes reported by an environment's apps, counted per minute."""

    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="flag_bisect_buckets",
    )
    minute = models.DateTimeField()
    total = models.PositiveIntegerField(default=0)
    failures = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["environment", "minute"],
                name="flag_bisect_unique_bucket_per_minute",
            )
        ]


class SignalSource(models.Model):
    """Reads outcomes from the Experimentation events an environment's apps already send.

    Each `failure_event` counts as a failed outcome and each `success_event` as a
    successful one, for the identity the event was sent for.
    """

    environment = models.OneToOneField(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="flag_bisect_signal_source",
    )
    failure_event = models.CharField(max_length=MAX_EVENT_NAME_CHARS)
    success_event = models.CharField(max_length=MAX_EVENT_NAME_CHARS)
    # The highest `SDKExperimentationEvent.id` already counted.
    last_event_id = models.BigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class Incident(models.Model):
    """A regression the swarm is investigating in one environment."""

    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="flag_bisect_incidents",
    )
    state = models.CharField(max_length=32, choices=IncidentState.choices)
    onset_at = models.DateTimeField()
    baseline_rate = models.FloatField()
    regression_rate = models.FloatField()
    # Bisection state: odds per hypothesis, as [[ids], p] pairs.
    beliefs = models.JSONField(default=list)
    rounds = models.PositiveIntegerField(default=0)
    conclusion = models.JSONField(null=True, blank=True)
    confirmed = models.BooleanField(default=False)

    # Gate 1: the envelope a person approved before anything changes in Flagsmith.
    canary_percent = models.PositiveSmallIntegerField(default=5)
    max_rounds = models.PositiveSmallIntegerField(default=12)
    max_minutes = models.PositiveSmallIntegerField(default=45)
    envelope_approved_by = models.ForeignKey(
        "users.FFAdminUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    envelope_approved_by_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    envelope_approved_at = models.DateTimeField(null=True, blank=True)
    canary_segment = models.ForeignKey(
        "segments.Segment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    # Gate 2: one person proposes the remediation, a different person approves it.
    remediation_proposed_by = models.ForeignKey(
        "users.FFAdminUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    remediation_proposed_by_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    remediation_approved_by = models.ForeignKey(
        "users.FFAdminUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    remediation_approved_by_api_key = models.ForeignKey(
        "api_keys.MasterAPIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    remediation_result = models.JSONField(null=True, blank=True)
    remediated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-id"]


class Suspect(models.Model):
    """A recent environment-default change to one feature."""

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="suspects"
    )
    feature = models.ForeignKey("features.Feature", on_delete=models.CASCADE)
    before_enabled = models.BooleanField()
    before_value = models.JSONField(null=True, blank=True)
    after_enabled = models.BooleanField()
    after_value = models.JSONField(null=True, blank=True)
    changed_at = models.DateTimeField()
    prior = models.FloatField(default=0.0)

    class Meta:
        ordering = ["changed_at", "id"]

    @property
    def key(self) -> str:
        return str(self.feature_id)


class Probe(models.Model):
    """One canary experiment: these suspects reverted for the canary segment only."""

    class Kind(models.TextChoices):
        BISECT = "BISECT"
        CONFIRM = "CONFIRM"

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="probes"
    )
    round = models.PositiveSmallIntegerField()
    kind = models.CharField(max_length=16, choices=Kind.choices)
    reverted = models.ManyToManyField(Suspect, related_name="probes")
    started_at = models.DateTimeField()
    settles_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    canary_total = models.PositiveIntegerField(default=0)
    canary_failures = models.PositiveIntegerField(default=0)
    main_total = models.PositiveIntegerField(default=0)
    main_failures = models.PositiveIntegerField(default=0)
    verdict = models.CharField(max_length=16, blank=True, default="")
    judgement = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["round"]
        constraints = [
            models.UniqueConstraint(
                fields=["incident", "round"], name="flag_bisect_unique_probe_round"
            )
        ]


class AgentMessage(models.Model):
    """What each agent of the swarm said, in order. The incident's trail."""

    class Agent(models.TextChoices):
        SENTINEL = "sentinel"
        ARCHIVIST = "archivist"
        PROFILER = "profiler"
        GUARDIAN = "guardian"
        PROBER = "prober"
        JUDGE = "judge"
        SCRIBE = "scribe"
        HUMAN = "human"

    incident = models.ForeignKey(
        Incident, on_delete=models.CASCADE, related_name="messages"
    )
    agent = models.CharField(max_length=16, choices=Agent.choices)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
