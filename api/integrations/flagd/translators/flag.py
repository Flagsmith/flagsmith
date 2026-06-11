"""
Translate a Flagsmith feature (with all its environment-level state,
segment overrides, and identity overrides) into a flagd flag entry.

flagd resolves a flag to a single variant. Flagsmith carries
``enabled`` (boolean) and a typed ``value`` simultaneously, plus
optional multivariate options and per-segment/identity overrides
that can each set their own typed value.

Mapping:

- ``control`` variant carrying the typed value (always present;
  the ``defaultVariant``).
- ``variant_1``, ``variant_2``, … for multivariate options.
- ``override_<segment-or-identity-slug>`` variants for each override
  whose value differs from the control. flagd targeting can only
  return a *variant key* (never a literal value), so the override's
  typed value has to live in a variant of its own.

The ``enabled`` field on an override is **not represented** in the
flagd output: flagd has no per-segment ``state`` concept, only values.
Operators expressing "off for this segment" should set the override
value explicitly (e.g. ``false`` for boolean flags). When a disabled
override carries a value identical to control we emit a translation
warning so the no-op is visible in the diagnostics endpoint.

The flag-level ``state`` field still reflects ``feature_state.enabled``
— so a disabled flag is reported as ``state: DISABLED`` and flagd's
SDK consumers can decide what to return for that case via the
``defaultVariant`` (always ``control``).
"""

from collections.abc import Iterable
from typing import Any

from integrations.flagd.constants import (
    VARIANT_CONTROL,
    WARNING_DISABLED_OVERRIDE_NO_OP,
    WARNING_IDENTITY_OVERRIDE_LIMIT,
)
from integrations.flagd.translators.multivariate import (
    collect_variants,
    fractional_jsonlogic,
)
from integrations.flagd.translators.segment import slugify_name
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

    # Mint per-override variants for overrides whose value differs from
    # control. Mutates ``variants`` in place and returns lookup tables
    # the targeting builder consults.
    segment_override_variants, identity_override_variants = _register_override_variants(
        feature_state.feature.id,
        control_value=control_value,
        segments=segments,
        segment_keys=segment_keys,
        identity_overrides=identity_overrides,
        variants=variants,
        feature_key=feature_key,
        warnings=warnings,
    )

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
        control_target=control_target,
        segment_override_variants=segment_override_variants,
        identity_override_variants=identity_override_variants,
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


def _register_override_variants(
    feature_id: int,
    *,
    control_value: Any,
    segments: Iterable[SegmentModel],
    segment_keys: dict[int, str],
    identity_overrides: Iterable[IdentityModel],
    variants: dict[str, Any],
    feature_key: str,
    warnings: list[TranslationWarning],
) -> tuple[dict[int, str], dict[str, str]]:
    """
    Walk the overrides on ``feature_id``. For each one carrying a typed
    value that differs from the control, mint a unique ``override_<slug>``
    variant and add it to ``variants``. Returns lookup tables segment-id
    → variant-name and identity-identifier → variant-name; absent keys
    mean "route to control".

    Overrides whose value matches the control are *no-ops* in flagd.
    When such an override is also marked ``enabled=False`` we emit a
    warning so the operator can see the discrepancy via the diagnostics
    endpoint.
    """
    taken: set[str] = set(variants.keys())
    segment_override_variants: dict[int, str] = {}
    identity_override_variants: dict[str, str] = {}

    for segment in segments:
        override_fs = _find_segment_override(segment, feature_id)
        if override_fs is None:
            continue
        if override_fs.feature_state_value == control_value:
            if not override_fs.enabled:
                warnings.append(
                    TranslationWarning(
                        reason=WARNING_DISABLED_OVERRIDE_NO_OP,
                        detail=(
                            f"feature={feature_key}, segment={segment.name}; "
                            "set the override value explicitly to change the "
                            "value flagd returns for this segment."
                        ),
                    )
                )
            continue
        slug_base = segment_keys.get(segment.id) or slugify_name(
            segment.name, fallback=f"segment-{segment.id}"
        )
        name = _unique_variant_name(f"override_{slug_base}", taken)
        taken.add(name)
        variants[name] = override_fs.feature_state_value
        segment_override_variants[segment.id] = name

    for identity in identity_overrides:
        override_fs = _find_identity_override(identity, feature_id)
        if override_fs is None:
            continue
        if override_fs.feature_state_value == control_value:
            if not override_fs.enabled:
                warnings.append(
                    TranslationWarning(
                        reason=WARNING_DISABLED_OVERRIDE_NO_OP,
                        detail=(
                            f"feature={feature_key}, identity={identity.identifier}; "
                            "set the override value explicitly to change the "
                            "value flagd returns for this identity."
                        ),
                    )
                )
            continue
        slug_base = slugify_name(identity.identifier, fallback="identity")
        name = _unique_variant_name(f"override_{slug_base}", taken)
        taken.add(name)
        variants[name] = override_fs.feature_state_value
        identity_override_variants[identity.identifier] = name

    return segment_override_variants, identity_override_variants


def _unique_variant_name(candidate: str, taken: set[str]) -> str:
    if candidate not in taken:
        return candidate
    counter = 2
    while True:
        suffixed = f"{candidate}-{counter}"
        if suffixed not in taken:
            return suffixed
        counter += 1


def _build_targeting(
    *,
    feature_state: FeatureStateModel,
    feature_key: str,
    segments: Iterable[SegmentModel],
    segment_targeting: dict[int, JsonLogic | None],
    segment_keys: dict[int, str],
    identity_overrides: Iterable[IdentityModel],
    identity_override_limit: int,
    control_target: Any,
    segment_override_variants: dict[int, str],
    identity_override_variants: dict[str, str],
    warnings: list[TranslationWarning],
) -> JsonLogic | None:
    feature_id = feature_state.feature.id

    # ----- Identity overrides (highest priority) ------------------------
    identity_branches: list[tuple[str, str]] = []
    overflow = 0
    for identity in identity_overrides:
        override_fs = _find_identity_override(identity, feature_id)
        if override_fs is None:
            continue
        variant = identity_override_variants.get(identity.identifier)
        if variant is None:
            # No-op override (value == control); nothing to route.
            continue
        if len(identity_branches) >= identity_override_limit:
            overflow += 1
            continue
        identity_branches.append((identity.identifier, variant))
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
    segment_branches: list[tuple[JsonLogic, str]] = []
    indexed_segments = list(segments)
    indexed_segments.sort(
        key=lambda s: _segment_override_priority(s, feature_id),
    )
    for segment in indexed_segments:
        variant = segment_override_variants.get(segment.id)
        if variant is None:
            continue
        targeting = segment_targeting.get(segment.id)
        if targeting is None:
            continue
        # Single-use segments are inlined; multi-use segments are
        # referenced via $ref into the document's $evaluators block.
        # The orchestrator decides which: when ``segment_keys`` has an
        # entry for this segment, the segment is shared and we route
        # through $ref.
        shared_key = segment_keys.get(segment.id)
        segment_logic: JsonLogic = (
            {"$ref": shared_key} if shared_key is not None else targeting
        )
        segment_branches.append((segment_logic, variant))

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
