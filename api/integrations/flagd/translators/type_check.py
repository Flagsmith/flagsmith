"""
Detect cross-variant type mismatches in a Flagsmith feature state
before flagd sees the resulting document.

flagd's JSON Schema defines four typed flags (boolean, number, string,
object); a single flag's variants must all share a type. Flagsmith
permits free-form values, so the same feature can legitimately mix
types — but for flagd consumption that's a misconfiguration which
either fails schema validation or surfaces as ``TYPE_MISMATCH`` at
OpenFeature evaluation time.

This module emits structured ``TranslationWarning``s that the diagnostic
endpoint can surface to operators (so they can fix the flag in the
Flagsmith UI before it bites a flagd consumer).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from integrations.flagd.types import TranslationWarning
from util.engine_models.features.models import FeatureStateModel
from util.engine_models.identities.models import IdentityModel
from util.engine_models.segments.models import SegmentModel

WARNING_TYPE_MISMATCH = "type_mismatch"


def _flagd_type(value: Any) -> str | None:
    """
    Bucket a Python value into one of flagd's typed-flag categories.
    Returns ``None`` for ``None`` (compatible with anything).
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "unknown"


def detect_type_mismatch(
    feature_state: FeatureStateModel,
    *,
    segments: Iterable[SegmentModel] = (),
    identity_overrides: Iterable[IdentityModel] = (),
) -> list[TranslationWarning]:
    """
    Return one ``TranslationWarning`` per type mismatch found across:
    - the feature state's control value
    - its multivariate option values
    - any segment override's control + multivariate values
    - any identity override's control + multivariate values

    Empty list when every value reachable through the flag shares a
    flagd type. ``None`` is treated as compatible with anything.
    """
    feature_id = feature_state.feature.id
    seen: dict[str, Any] = {}

    def _ingest(value: Any) -> None:
        type_ = _flagd_type(value)
        if type_ is None or type_ in seen:
            return
        seen[type_] = value

    def _ingest_feature_state(fs: FeatureStateModel) -> None:
        _ingest(fs.feature_state_value)
        for mv_value in fs.multivariate_feature_state_values:
            _ingest(mv_value.multivariate_feature_option.value)

    _ingest_feature_state(feature_state)
    for segment in segments:
        for fs in segment.feature_states:
            if fs.feature.id == feature_id:
                _ingest_feature_state(fs)
    for identity in identity_overrides:
        for fs in identity.identity_features:
            if fs.feature.id == feature_id:
                _ingest_feature_state(fs)

    if len(seen) <= 1:
        return []

    types_summary = ", ".join(sorted(seen.keys()))
    return [
        TranslationWarning(
            reason=WARNING_TYPE_MISMATCH,
            detail=(f"feature={feature_state.feature.name}, types=[{types_summary}]"),
        )
    ]
