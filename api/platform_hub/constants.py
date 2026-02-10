from __future__ import annotations

from typing import Any

# Each entry: (ModelClass, org_lookup_path, scope)
# Using Any for model class to avoid mypy issues with Django model managers.
type IntegrationEntry = tuple[Any, str, str]


def get_integration_registry() -> dict[str, IntegrationEntry]:
    """Return the registry of integration models, lazily imported to avoid circular imports."""
    from integrations.amplitude.models import AmplitudeConfiguration
    from integrations.datadog.models import DataDogConfiguration
    from integrations.dynatrace.models import DynatraceConfiguration
    from integrations.github.models import GithubConfiguration
    from integrations.grafana.models import (
        GrafanaOrganisationConfiguration,
        GrafanaProjectConfiguration,
    )
    from integrations.heap.models import HeapConfiguration
    from integrations.mixpanel.models import MixpanelConfiguration
    from integrations.new_relic.models import NewRelicConfiguration
    from integrations.rudderstack.models import RudderstackConfiguration
    from integrations.segment.models import SegmentConfiguration
    from integrations.sentry.models import SentryChangeTrackingConfiguration
    from integrations.slack.models import SlackConfiguration
    from integrations.webhook.models import WebhookConfiguration

    return {
        "amplitude": (
            AmplitudeConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "dynatrace": (
            DynatraceConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "heap": (
            HeapConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "mixpanel": (
            MixpanelConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "rudderstack": (
            RudderstackConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "segment": (
            SegmentConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "sentry": (
            SentryChangeTrackingConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "webhook": (
            WebhookConfiguration,
            "environment__project__organisation_id",
            "environment",
        ),
        "datadog": (
            DataDogConfiguration,
            "project__organisation_id",
            "project",
        ),
        "new-relic": (
            NewRelicConfiguration,
            "project__organisation_id",
            "project",
        ),
        "slack": (
            SlackConfiguration,
            "project__organisation_id",
            "project",
        ),
        "grafana-project": (
            GrafanaProjectConfiguration,
            "project__organisation_id",
            "project",
        ),
        "github": (
            GithubConfiguration,
            "organisation_id",
            "organisation",
        ),
        "grafana": (
            GrafanaOrganisationConfiguration,
            "organisation_id",
            "organisation",
        ),
    }
