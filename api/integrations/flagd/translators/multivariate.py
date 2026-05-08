"""
Translate Flagsmith multivariate options into a flagd ``fractional``
expression. flagd performs the actual bucketing — we only encode the
weights and per-feature seed.
"""

from typing import Any

from integrations.flagd.types import JsonLogic
from util.engine_models.features.models import FeatureStateModel


def fractional_jsonlogic(
    feature_state: FeatureStateModel,
    *,
    feature_key: str,
    variant_keys: dict[int, str],
    control_variant: str,
) -> JsonLogic:
    """
    Build a flagd ``fractional`` expression. ``variant_keys`` maps a
    multivariate option id (or its uuid as fallback) to the variant
    name used in the parent flag's ``variants`` block.

    The residual percentage (i.e. ``100 - sum(allocations)``) is routed
    to ``control_variant`` so behaviour matches Flagsmith's model where
    the unallocated slice resolves to the feature state's value.
    """
    weights: list[list[Any]] = []
    total_allocation = 0.0

    for mv_value in feature_state.multivariate_feature_state_values:
        identifier = mv_value.id or str(mv_value.mv_fs_value_uuid)
        variant = variant_keys[identifier]
        weight = float(mv_value.percentage_allocation)
        if weight <= 0:
            continue
        weights.append([variant, weight])
        total_allocation += weight

    residual = max(0.0, 100.0 - total_allocation)
    if residual > 0:
        weights.append([control_variant, residual])

    bucket_seed: JsonLogic = {
        "cat": [{"var": "targetingKey"}, feature_key],
    }

    return {"fractional": [bucket_seed, *weights]}


def collect_variants(
    feature_state: FeatureStateModel,
    *,
    control_variant: str,
    control_value: Any,
) -> tuple[dict[str, Any], dict[Any, str]]:
    """
    Return ``(variants, variant_keys)``:
    - ``variants`` maps variant name → resolved value, suitable for
      flagd's ``variants`` block.
    - ``variant_keys`` maps the multivariate option id (or uuid) → the
      generated variant name.
    """
    variants: dict[str, Any] = {control_variant: control_value}
    variant_keys: dict[Any, str] = {}
    for index, mv_value in enumerate(
        feature_state.multivariate_feature_state_values, start=1
    ):
        name = f"variant_{index}"
        identifier = mv_value.id or str(mv_value.mv_fs_value_uuid)
        variants[name] = mv_value.multivariate_feature_option.value
        variant_keys[identifier] = name
    return variants, variant_keys
