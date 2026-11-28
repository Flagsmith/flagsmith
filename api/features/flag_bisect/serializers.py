import typing

from rest_framework import serializers

from experimentation.constants import MAX_EVENT_NAME_CHARS
from features.flag_bisect import services
from features.flag_bisect.models import (
    AgentMessage,
    Incident,
    Probe,
    Suspect,
)

MAX_SIGNALS = services.MAX_SIGNALS_PER_REQUEST


class SignalSerializer(serializers.Serializer[dict[str, typing.Any]]):
    identifier = serializers.CharField(max_length=2000)
    ok = serializers.BooleanField()


class SignalsRequestSerializer(serializers.Serializer[dict[str, typing.Any]]):
    signals = serializers.ListField(
        child=SignalSerializer(), min_length=1, max_length=MAX_SIGNALS
    )


class SuspectSerializer(serializers.ModelSerializer[Suspect]):
    feature_name = serializers.CharField(source="feature.name", read_only=True)
    posterior = serializers.SerializerMethodField()

    class Meta:
        model = Suspect
        fields = (
            "id",
            "feature",
            "feature_name",
            "before_enabled",
            "before_value",
            "after_enabled",
            "after_value",
            "changed_at",
            "prior",
            "posterior",
        )

    def get_posterior(self, suspect: Suspect) -> float:
        return float(self.context["posteriors"].get(suspect.key, 0.0))


class ProbeSerializer(serializers.ModelSerializer[Probe]):
    reverted_features = serializers.SerializerMethodField()

    class Meta:
        model = Probe
        fields = (
            "round",
            "kind",
            "reverted_features",
            "started_at",
            "settles_at",
            "ended_at",
            "canary_total",
            "canary_failures",
            "main_total",
            "main_failures",
            "verdict",
            "judgement",
        )

    def get_reverted_features(self, probe: Probe) -> list[str]:
        return [s.feature.name for s in probe.reverted.all()]


class AgentMessageSerializer(serializers.ModelSerializer[AgentMessage]):
    class Meta:
        model = AgentMessage
        fields = ("agent", "text", "created_at")


class IncidentListSerializer(serializers.ModelSerializer[Incident]):
    class Meta:
        model = Incident
        fields: tuple[str, ...] = (
            "id",
            "state",
            "onset_at",
            "baseline_rate",
            "regression_rate",
            "rounds",
            "conclusion",
            "confirmed",
            "created_at",
            "updated_at",
        )


class IncidentSerializer(IncidentListSerializer):
    suspects = serializers.SerializerMethodField()
    probes = ProbeSerializer(many=True, read_only=True)
    messages = AgentMessageSerializer(many=True, read_only=True)
    hypotheses = serializers.SerializerMethodField()

    class Meta(IncidentListSerializer.Meta):
        fields = IncidentListSerializer.Meta.fields + (
            "canary_percent",
            "max_rounds",
            "max_minutes",
            "envelope_approved_at",
            "canary_segment",
            "remediation_result",
            "suspects",
            "probes",
            "messages",
            "hypotheses",
        )

    def get_suspects(self, incident: Incident) -> list[dict[str, typing.Any]]:
        context = {"posteriors": services.posteriors(incident)}
        return SuspectSerializer(
            incident.suspects.all(), many=True, context=context
        ).data  # type: ignore[return-value]

    def get_hypotheses(self, incident: Incident) -> list[dict[str, typing.Any]]:
        names = {s.key: s.feature.name for s in incident.suspects.all()}
        return [
            {"features": [names.get(i, i) for i in ids], "probability": p}
            for ids, p in services.hypotheses(incident)
        ]


class EnvelopeSerializer(serializers.Serializer[dict[str, typing.Any]]):
    canary_percent = serializers.IntegerField(min_value=1, max_value=20, required=False)
    max_rounds = serializers.IntegerField(min_value=1, max_value=20, required=False)
    max_minutes = serializers.IntegerField(min_value=5, max_value=240, required=False)


class ReasonSerializer(serializers.Serializer[dict[str, typing.Any]]):
    reason = serializers.CharField(min_length=5, max_length=500)


class SignalSourceSerializer(serializers.Serializer[dict[str, typing.Any]]):
    failure_event = serializers.CharField(max_length=MAX_EVENT_NAME_CHARS)
    success_event = serializers.CharField(max_length=MAX_EVENT_NAME_CHARS)

    def validate(self, data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        for field in ("failure_event", "success_event"):
            if data[field].startswith("$"):
                raise serializers.ValidationError(
                    {field: "Use the name of an event your app sends."}
                )
        if data["failure_event"] == data["success_event"]:
            raise serializers.ValidationError(
                {"success_event": "Must differ from the failure event."}
            )
        return data


class SignalSourceResponseSerializer(serializers.Serializer[dict[str, typing.Any]]):
    failure_event = serializers.CharField(allow_null=True)
    success_event = serializers.CharField(allow_null=True)
    events_stored_in_flagsmith = serializers.BooleanField()
