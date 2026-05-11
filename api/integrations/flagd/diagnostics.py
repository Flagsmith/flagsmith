"""
Per-environment translation diagnostics.

Reuses the same translation pipeline as the sync endpoint to surface
issues that would degrade flagd consumption (type mismatches, unsupported
operators, identity-override cap overflow). Operators can curl the
diagnostics endpoint to audit an environment, alert on warnings in
their CI pipeline, or build their own dashboard against the JSON.

This module deliberately lives alongside ``services.py`` rather than
inside it so the diagnostic path can evolve independently of the
hot-path sync builder.
"""

from __future__ import annotations

from typing import Any

import structlog

from integrations.flagd.constants import (
    DEFAULT_IDENTITY_OVERRIDE_LIMIT,
    FLAGD_TRANSLATOR_VERSION,
)
from integrations.flagd.translators.flag import feature_state_to_flagd_flag
from integrations.flagd.translators.segment import (
    segment_to_jsonlogic,
    slugify_name,
    slugify_segment_name,
)
from integrations.flagd.translators.type_check import detect_type_mismatch
from integrations.flagd.types import TranslationWarning
from util.engine_models.environments.models import EnvironmentModel
from util.mappers.engine import map_environment_to_engine
from django.conf import settings

logger = structlog.get_logger("flagd_sync")


def diagnose_environment(environment: Any) -> dict[str, Any]:
    """
    Run the translator over ``environment`` purely to collect warnings.
    Returns a structured report keyed by feature name plus an
    environment-level summary.
    """
    engine_environment: EnvironmentModel = map_environment_to_engine(
        environment, with_integrations=False
    )
    project = environment.project
    identity_override_limit = getattr(
        settings,
        "FLAGD_SYNC_IDENTITY_OVERRIDE_LIMIT",
        DEFAULT_IDENTITY_OVERRIDE_LIMIT,
    )

    # Translate segments once so flag translation can reuse the cache.
    segments = engine_environment.project.segments
    segment_warnings: list[TranslationWarning] = []
    segment_keys: dict[int, str] = {}
    segment_targeting: dict[int, Any] = {}
    used: set[str] = set()
    for segment in segments:
        key = slugify_segment_name(segment.name, taken=used)
        used.add(key)
        segment_keys[segment.id] = key
        segment_targeting[segment.id] = segment_to_jsonlogic(
            segment, warnings=segment_warnings
        )

    default_feature_states = [
        fs
        for fs in engine_environment.feature_states
        if fs.feature_segment is None
    ]

    features: list[dict[str, Any]] = []
    for fs in default_feature_states:
        per_feature_warnings: list[TranslationWarning] = []

        # Type-consistency check — flagd's JSON Schema requires variants
        # of one flag to share a type. This catches it pre-emptively so
        # operators see a clear warning rather than a TYPE_MISMATCH at
        # evaluation time. We include segment + identity override values
        # because an override can legitimately introduce a different type
        # (e.g. a number override on a string flag).
        per_feature_warnings.extend(
            detect_type_mismatch(
                fs,
                segments=segments,
                identity_overrides=engine_environment.identity_overrides,
            )
        )

        # Run the regular translator just to capture operator-level
        # warnings (REGEX skipped, identity-override cap, malformed
        # values, etc.). We don't keep the resulting flag here — the
        # sync endpoint owns that path.
        feature_state_to_flagd_flag(
            fs,
            feature_key=fs.feature.name,
            segments=segments,
            segment_targeting=segment_targeting,
            segment_keys=segment_keys,
            identity_overrides=engine_environment.identity_overrides,
            identity_override_limit=identity_override_limit,
            warnings=per_feature_warnings,
        )

        if per_feature_warnings:
            features.append(
                {
                    "name": fs.feature.name,
                    "warnings": list(per_feature_warnings),
                }
            )

    flag_set_id = (
        f"{slugify_name(project.name)}/{slugify_name(environment.name)}"
    )
    return {
        "flagSetId": flag_set_id,
        "translatorVersion": FLAGD_TRANSLATOR_VERSION,
        "environmentWarnings": list(segment_warnings),
        "features": features,
        "summary": {
            "featuresWithWarnings": len(features),
            "totalWarnings": sum(len(f["warnings"]) for f in features)
            + len(segment_warnings),
        },
    }


__all__ = ("diagnose_environment",)
