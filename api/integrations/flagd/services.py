"""
Build flagd-compatible flag-definition documents from Flagsmith
environments.

The service is a thin orchestrator over the per-feature, per-segment
translators. It deliberately consumes the engine document
(``EnvironmentModel``) so that the data shape stays aligned with what
SDK local evaluation already operates on.
"""

import json
from typing import Any

import structlog
from django.conf import settings

from integrations.flagd.constants import (
    DEFAULT_IDENTITY_OVERRIDE_LIMIT,
    FLAGD_SCHEMA_URL,
    FLAGD_TRANSLATOR_VERSION,
)
from integrations.flagd.metrics import (
    flagsmith_flagd_translation_warnings_total,
)
from integrations.flagd.translators.flag import feature_state_to_flagd_flag
from integrations.flagd.translators.segment import (
    segment_to_jsonlogic,
    slugify_name,
    slugify_segment_name,
)
from integrations.flagd.types import FlagdDocument, JsonLogic, TranslationWarning
from util.engine_models.environments.models import EnvironmentModel
from util.mappers.engine import map_environment_to_engine

logger = structlog.get_logger("flagd_sync")


def build_flagd_document(environment: Any) -> dict[str, Any]:
    """
    Translate a Django ``Environment`` instance into the flagd
    flag-definition document.
    """
    engine_environment: EnvironmentModel = map_environment_to_engine(
        environment, with_integrations=False
    )
    project = environment.project
    flag_set_id = f"{slugify_name(project.name)}/{slugify_name(environment.name)}"
    version = (
        environment.updated_at.isoformat() if environment.updated_at else "0"
    )
    return _build_from_engine(
        engine_environment,
        environment_id=environment.id,
        flag_set_id=flag_set_id,
        version=version,
    )


def _build_from_engine(
    engine_environment: EnvironmentModel,
    *,
    environment_id: int,
    flag_set_id: str,
    version: str,
) -> dict[str, Any]:
    warnings: list[TranslationWarning] = []
    identity_override_limit = getattr(
        settings,
        "FLAGD_SYNC_IDENTITY_OVERRIDE_LIMIT",
        DEFAULT_IDENTITY_OVERRIDE_LIMIT,
    )

    # Translate segments once. Each segment yields a JsonLogic expression
    # to be referenced from flag targeting via $evaluators / $ref.
    segments = engine_environment.project.segments
    segment_keys: dict[int, str] = {}
    segment_targeting: dict[int, JsonLogic | None] = {}
    used_keys: set[str] = set()
    evaluators: dict[str, JsonLogic] = {}
    for segment in segments:
        key = slugify_segment_name(segment.name, taken=used_keys)
        used_keys.add(key)
        segment_keys[segment.id] = key
        targeting = segment_to_jsonlogic(segment, warnings=warnings)
        segment_targeting[segment.id] = targeting
        if targeting is not None:
            evaluators[key] = targeting

    # Default feature states are those without a feature_segment and
    # without an identity. The engine document carries them on
    # environment.feature_states; per-segment overrides live on
    # segment.feature_states (already separate).
    default_feature_states = [
        fs
        for fs in engine_environment.feature_states
        if fs.feature_segment is None
    ]

    flags: dict[str, Any] = {}
    for fs in default_feature_states:
        feature_key = fs.feature.name
        flag = feature_state_to_flagd_flag(
            fs,
            feature_key=feature_key,
            segments=segments,
            segment_targeting=segment_targeting,
            segment_keys=segment_keys,
            identity_overrides=engine_environment.identity_overrides,
            identity_override_limit=identity_override_limit,
            warnings=warnings,
        )
        flags[feature_key] = flag

    document: dict[str, Any] = {
        "$schema": FLAGD_SCHEMA_URL,
        "flags": flags,
    }
    if evaluators:
        document["$evaluators"] = evaluators

    metadata: dict[str, Any] = {
        "flagSetId": flag_set_id,
        "version": version,
        "flagsmith.environmentId": environment_id,
        "flagsmith.translatorVersion": FLAGD_TRANSLATOR_VERSION,
    }
    if warnings:
        # flagd's metadata schema only accepts string/number/boolean
        # values. Serialise the warning list as a compact JSON string
        # so consumers can still parse it.
        metadata["flagsmith.warnings"] = json.dumps(list(warnings))
        for warning in warnings:
            flagsmith_flagd_translation_warnings_total.labels(
                reason=warning["reason"]
            ).inc()
        logger.info(
            "translation.warnings",
            environment__id=environment_id,
            warnings__count=len(warnings),
        )
    document["metadata"] = metadata

    return document


__all__ = ("build_flagd_document",)
