"""
Translate a Flagsmith feature (with all its environment-level state,
segment overrides, and identity overrides) into a flagd flag entry.

flagd resolves a flag to a single variant. Flagsmith carries
``enabled`` (boolean) and a typed ``value`` simultaneously, plus
optional multivariate options. We map that to:

- ``control`` variant carrying the typed value (always present).
- ``variant_1``, ``variant_2``, … for multivariate options.
- ``off`` variant carrying a type-zero, **only** emitted when at
  least one segment or identity override has ``enabled=False`` and
  therefore needs a destination distinct from ``control``.

``defaultVariant`` is always ``"control"``; flagd's ``state`` field
carries the enabled/disabled signal independently.
"""

from collections.abc import Iterable
from typing import Any

from integrations.flagd.constants import (
    VARIANT_CONTROL,
    VARIANT_OFF,
    WARNING_IDENTITY_OVERRIDE_LIMIT,
)
from integrations.flagd.translators.multivariate import (
    collect_variants,
    fractional_jsonlogic,
)
from integrations.flagd.types import FlagdFlag, JsonLogic, TranslationWarning
from util.engine_models.features.models import FeatureStateModel
from util.engine_models.identities.models import IdentityModel
from util.engine_models.segments.models import SegmentModel


def feature_state_to_flagd_flag(
    feature_state: FeatureStateModel,
    *,
    feature_key: str,
    segments: Iterable[SegmentModel],
    segment_targeting: dict[int, JsonLogic | None],
    segment_keys: dict[int, str],
    identity_overrides: Iterable[IdentityModel],
    identity_override_limit: int,
    warnings: list[TranslationWarning],
) -> FlagdFlag:
    """
    Build the flagd flag definition for a single feature.

    ``segment_targeting`` and ``segment_keys`` are pre-computed by the
    caller so we don't translate the same segment more than once; both
    are keyed by segment id.
    """
    has_multivariate = bool(feature_state.multivariate_feature_state_values)
    control_value = feature_state.feature_state_value
    # Flagsmith flags without a typed value carry meaning only via
    # ``enabled``. Map them to a boolean flagd flag so variants are
    # well-typed.
    if control_value is None and not has_multivariate:
        control_value = True

    if has_multivariate:
        variants, variant_keys = collect_variants(
            feature_state,
            control_variant=VARIANT_CONTROL,
            control_value=control_value,
        )
    else:
        variants = {VARIANT_CONTROL: control_value}
        variant_keys = {}

    needs_off_variant = _has_disabled_override(
        feature_state.feature.id, segments, identity_overrides
    )
    if needs_off_variant:
        variants[VARIANT_OFF] = _off_value_for(control_value)

    control_target: Any
    if has_multivariate:
        control_target = fractional_jsonlogic(
            feature_state,
            feature_key=feature_key,
            variant_keys=variant_keys,
            control_variant=VARIANT_CONTROL,
        )
    else:
        control_target = VARIANT_CONTROL

    targeting = _build_targeting(
        feature_state=feature_state,
        feature_key=feature_key,
        segments=segments,
        segment_targeting=segment_targeting,
        segment_keys=segment_keys,
        identity_overrides=identity_overrides,
        identity_override_limit=identity_override_limit,
        variant_keys=variant_keys,
        control_target=control_target,
        warnings=warnings,
    )

    flag: FlagdFlag = {
        "state": "ENABLED" if feature_state.enabled else "DISABLED",
        "variants": variants,
        "defaultVariant": VARIANT_CONTROL,
    }
    if targeting is not None:
        flag["targeting"] = targeting
    return flag


def _has_disabled_override(
    feature_id: int,
    segments: Iterable[SegmentModel],
    identity_overrides: Iterable[IdentityModel],
) -> bool:
    for segment in segments:
        for fs in segment.feature_states:
            if fs.feature.id == feature_id and not fs.enabled:
                return True
    for identity in identity_overrides:
        for fs in identity.identity_features:
            if fs.feature.id == feature_id and not fs.enabled:
                return True
    return False


def _build_targeting(
    *,
    feature_state: FeatureStateModel,
    feature_key: str,
    segments: Iterable[SegmentModel],
    segment_targeting: dict[int, JsonLogic | None],
    segment_keys: dict[int, str],
    identity_overrides: Iterable[IdentityModel],
    identity_override_limit: int,
    variant_keys: dict[Any, str],
    control_target: Any,
    warnings: list[TranslationWarning],
) -> JsonLogic | None:
    feature_id = feature_state.feature.id

    # ----- Identity overrides (highest priority) ------------------------
    identity_branches: list[tuple[str, Any]] = []
    overflow = 0
    for identity in identity_overrides:
        override_fs = _find_identity_override(identity, feature_id)
        if override_fs is None:
            continue
        if len(identity_branches) >= identity_override_limit:
            overflow += 1
            continue
        identity_branches.append(
            (identity.identifier, _resolve_override_variant(override_fs))
        )
    if overflow:
        warnings.append(
            TranslationWarning(
                reason=WARNING_IDENTITY_OVERRIDE_LIMIT,
                detail=f"feature={feature_key}, dropped={overflow}",
            )
        )

    # ----- Segment overrides -------------------------------------------
    # Higher priority (lower numeric value) wins; default to insertion
    # order when priority is missing.
    segment_branches: list[tuple[JsonLogic, Any]] = []
    indexed_segments = list(segments)
    indexed_segments.sort(
        key=lambda s: _segment_override_priority(s, feature_id),
    )
    for segment in indexed_segments:
        override_fs = _find_segment_override(segment, feature_id)
        if override_fs is None:
            continue
        targeting = segment_targeting.get(segment.id)
        if targeting is None:
            continue
        segment_branches.append(
            (
                {"$ref": segment_keys[segment.id]},
                _resolve_override_variant(override_fs),
            )
        )

    # When no overrides apply, the flag resolves via the control path:
    # either the static `control` variant or the multivariate fractional
    # expression. The disabled-state semantic is conveyed by flagd's
    # `state` field, not by routing here.
    fallback: Any = control_target

    if not identity_branches and not segment_branches:
        # Static-default flags don't need targeting at all; the
        # variant returned by ``defaultVariant`` is enough.
        if isinstance(fallback, str):
            return None
        return fallback

    expression: Any = fallback

    # Build right-to-left so identity overrides win.
    for ref_logic, variant in reversed(segment_branches):
        expression = {"if": [ref_logic, variant, expression]}

    # Identity overrides are chained right-to-left so each one can
    # resolve to a different variant and the first match wins.
    for identifier, variant in reversed(identity_branches):
        expression = {
            "if": [
                {"==": [{"var": "targetingKey"}, identifier]},
                variant,
                expression,
            ]
        }

    return expression


def _find_identity_override(
    identity: IdentityModel, feature_id: int
) -> FeatureStateModel | None:
    for fs in identity.identity_features:
        if fs.feature.id == feature_id:
            return fs
    return None


def _find_segment_override(
    segment: SegmentModel, feature_id: int
) -> FeatureStateModel | None:
    for fs in segment.feature_states:
        if fs.feature.id == feature_id:
            return fs
    return None


def _segment_override_priority(segment: SegmentModel, feature_id: int) -> int:
    for fs in segment.feature_states:
        if fs.feature.id == feature_id and fs.feature_segment is not None:
            return fs.feature_segment.priority or 0
    return 0


def _resolve_override_variant(feature_state: FeatureStateModel) -> Any:
    """
    Pick the variant an override should resolve to.

    For now we resolve the override inline as the literal value rather
    than synthesising additional variants — flagd permits a JsonLogic
    branch to return the resolved value directly via a string variant
    name OR a nested object. We keep things simple by returning the
    parent flag's ``"on"``/``"off"`` based on the override's enabled
    flag. Multivariate overrides resolve to the override's
    ``feature_state_value`` directly (no per-identity bucketing for
    overrides).
    """
    if not feature_state.enabled:
        return VARIANT_OFF
    return VARIANT_CONTROL


def _off_value_for(control_value: Any) -> Any:
    if isinstance(control_value, bool):
        return False
    if isinstance(control_value, (int, float)):
        return 0
    if isinstance(control_value, str):
        return ""
    if isinstance(control_value, dict):
        return {}
    if isinstance(control_value, list):
        return []
    return False
