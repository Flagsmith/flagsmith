"""
Experiment results analytics.

This module provides endpoints for analysing A/B test (experiment) results
using trait-based tracking. Simple binary outcome: converted or not.

Usage:
1. When user sees a feature variant, set trait: `exp_{feature}_variant: "{value}"`
2. When user converts, set trait: `exp_{feature}_converted: true`
3. Query this endpoint to get conversion rates and statistical significance.

Example:
    # SDK side
    flagsmith.setTrait("exp_checkout_button_variant", "green")
    flagsmith.setTrait("exp_checkout_button_converted", true)

    # Query results
    GET /api/v1/environments/{env}/experiments/results/?feature=checkout_button
"""

import math
import random
from typing import Any

from common.environments.permissions import VIEW_ENVIRONMENT
from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from environments.identities.traits.models import Trait
from environments.models import Environment


class ExperimentVariantResultSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for individual variant results."""

    variant = serializers.CharField()
    evaluations = serializers.IntegerField()
    conversions = serializers.IntegerField()
    conversion_rate = serializers.FloatField()


class ExperimentStatisticsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for statistical analysis results."""

    p_value = serializers.FloatField()
    significant = serializers.BooleanField()
    chance_to_win = serializers.DictField(child=serializers.FloatField())
    lift = serializers.CharField()
    winner = serializers.CharField(allow_null=True)
    recommendation = serializers.CharField()
    sample_size_warning = serializers.CharField(allow_null=True, required=False)


class ExperimentResultsSerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for the full experiment results response."""

    feature = serializers.CharField()
    variants = ExperimentVariantResultSerializer(many=True)
    statistics = ExperimentStatisticsSerializer()


class ExperimentResultsQuerySerializer(serializers.Serializer):  # type: ignore[type-arg]
    """Serializer for experiment results query parameters."""

    feature = serializers.CharField(
        required=True,
        max_length=200,
        help_text="The feature name to analyse (without the 'exp_' prefix)",
    )


def calculate_statistics(results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """
    Calculate statistical significance using G-test and Bayesian methods.

    Args:
        results: Dictionary mapping variant names to their metrics
                 (total, conversions, rate)

    Returns:
        Dictionary containing p_value, chance_to_win, lift, and recommendations
    """
    variants = list(results.keys())

    if len(variants) == 0:
        return {
            "p_value": 1.0,
            "significant": False,
            "chance_to_win": {},
            "lift": "N/A",
            "winner": None,
            "recommendation": "No experiment data found",
            "sample_size_warning": None,
        }

    if len(variants) == 1:
        variant = variants[0]
        return {
            "p_value": 1.0,
            "significant": False,
            "chance_to_win": {variant: 1.0},
            "lift": "N/A",
            "winner": None,
            "recommendation": "Need at least 2 variants for comparison",
            "sample_size_warning": None,
        }

    if len(variants) == 2:
        return _calculate_two_variant_stats(results, variants)

    return _calculate_multi_variant_stats(results, variants)


def _get_sample_size_warning(min_sample: int) -> str | None:
    """Return a sample size warning if the sample is too small."""
    if min_sample < 30:
        return f"Low sample size ({min_sample}) - results may be unreliable"
    if min_sample < 100:
        return f"Sample size ({min_sample}) is modest - consider collecting more data"
    return None


def _calculate_two_variant_stats(
    results: dict[str, dict[str, Any]], variants: list[str]
) -> dict[str, Any]:
    """Calculate statistics for a two-variant experiment."""
    a, b = variants[0], variants[1]

    # Check for sufficient data
    total_a = results[a]["total"]
    total_b = results[b]["total"]

    if total_a == 0 or total_b == 0:
        return {
            "p_value": 1.0,
            "significant": False,
            "chance_to_win": {a: 0.5, b: 0.5},
            "lift": "N/A",
            "winner": None,
            "recommendation": "Insufficient data - one or more variants have no samples",
            "sample_size_warning": "One or more variants have zero samples",
        }

    # Build contingency table, replacing zeros with 0.5 to avoid log(0)
    table = [
        [
            max(results[a]["conversions"], 0.5),
            max(total_a - results[a]["conversions"], 0.5),
        ],
        [
            max(results[b]["conversions"], 0.5),
            max(total_b - results[b]["conversions"], 0.5),
        ],
    ]

    # G-test (log-likelihood ratio test)
    p_value = _g_test(table)

    # Bayesian "Chance to Win" using Monte Carlo simulation
    n_samples = 10000
    a_wins = 0
    alpha_a = results[a]["conversions"] + 1
    beta_a = total_a - results[a]["conversions"] + 1
    alpha_b = results[b]["conversions"] + 1
    beta_b = total_b - results[b]["conversions"] + 1
    for _ in range(n_samples):
        sa = random.betavariate(alpha_a, beta_a)
        sb = random.betavariate(alpha_b, beta_b)
        if sa > sb:
            a_wins += 1
    chance_a_wins = a_wins / n_samples

    # Determine winner and calculate lift (winner vs loser)
    if results[a]["rate"] > results[b]["rate"]:
        winner = a
        loser = b
    else:
        winner = b
        loser = a

    if results[loser]["rate"] > 0:
        lift = (results[winner]["rate"] - results[loser]["rate"]) / results[loser][
            "rate"
        ]
        lift_str = f"{lift:+.1%}"
    else:
        lift_str = "N/A"
    is_significant = bool(p_value < 0.05)

    if is_significant:
        recommendation = (
            f"{winner} wins with {max(chance_a_wins, 1 - chance_a_wins):.1%} confidence"
        )
    else:
        recommendation = "Keep collecting data - not yet significant"

    return {
        "p_value": round(float(p_value), 4),
        "significant": is_significant,
        "chance_to_win": {
            a: round(chance_a_wins, 3),
            b: round(1 - chance_a_wins, 3),
        },
        "lift": lift_str,
        "winner": winner if is_significant else None,
        "recommendation": recommendation,
        "sample_size_warning": _get_sample_size_warning(min(total_a, total_b)),
    }


def _calculate_multi_variant_stats(
    results: dict[str, dict[str, Any]], variants: list[str]
) -> dict[str, Any]:
    """Calculate statistics for experiments with 3+ variants."""
    # Check for sufficient data
    for v in variants:
        if results[v]["total"] == 0:
            return {
                "p_value": 1.0,
                "significant": False,
                "chance_to_win": {var: 1.0 / len(variants) for var in variants},
                "lift": "N/A",
                "winner": None,
                "recommendation": f"Insufficient data - variant '{v}' has no samples",
                "sample_size_warning": f"Variant '{v}' has zero samples",
            }

    # Build contingency table, replacing zeros with 0.5 to avoid log(0)
    table = [
        [
            max(results[v]["conversions"], 0.5),
            max(results[v]["total"] - results[v]["conversions"], 0.5),
        ]
        for v in variants
    ]

    # G-test
    p_value = _g_test(table)

    # Bayesian chance to win for each variant via Monte Carlo
    n_samples = 10000
    params = [
        (
            results[v]["conversions"] + 1,
            results[v]["total"] - results[v]["conversions"] + 1,
        )
        for v in variants
    ]
    win_counts = [0] * len(variants)
    for _ in range(n_samples):
        draws = [random.betavariate(a, b) for a, b in params]
        best_idx = max(range(len(draws)), key=lambda i: draws[i])
        win_counts[best_idx] += 1

    chance_to_win = {
        v: round(win_counts[i] / n_samples, 3) for i, v in enumerate(variants)
    }

    # Find the best performing variant
    best_variant = max(variants, key=lambda v: results[v]["rate"])
    is_significant = bool(p_value < 0.05)
    recommendation = (
        f"{best_variant} leads with {chance_to_win[best_variant]:.1%} chance to win"
        if is_significant
        else "Keep collecting data - not yet significant"
    )
    min_sample = min(results[v]["total"] for v in variants)

    return {
        "p_value": round(float(p_value), 4),
        "significant": is_significant,
        "chance_to_win": chance_to_win,
        "lift": "See individual rates",
        "winner": best_variant if is_significant else None,
        "recommendation": recommendation,
        "sample_size_warning": _get_sample_size_warning(min_sample),
    }


def _g_test(table: list[list[float]]) -> float:
    """
    Perform a G-test (log-likelihood ratio test) on a contingency table.

    Returns the p-value under the chi-squared distribution.
    """
    rows = len(table)
    cols = len(table[0])

    row_totals = [sum(row) for row in table]
    col_totals = [sum(table[r][c] for r in range(rows)) for c in range(cols)]
    grand_total = sum(row_totals)

    if grand_total == 0:  # pragma: no cover
        return 1.0

    g = 0.0
    for r in range(rows):
        for c in range(cols):
            observed = table[r][c]
            expected = row_totals[r] * col_totals[c] / grand_total
            if observed > 0 and expected > 0:
                g += observed * math.log(observed / expected)
    g *= 2

    df = (rows - 1) * (cols - 1)
    if df == 0:  # pragma: no cover
        return 1.0

    return _chi2_sf(g, df)


def _chi2_sf(x: float, df: int) -> float:
    """Survival function (1 - CDF) for the chi-squared distribution."""
    if x <= 0:
        return 1.0
    return _upper_gamma_reg(df / 2.0, x / 2.0)


def _upper_gamma_reg(a: float, x: float) -> float:
    """Regularised upper incomplete gamma function Q(a, x)."""
    if x <= 0:  # pragma: no cover
        return 1.0
    if x < a + 1:
        return 1.0 - _lower_gamma_series(a, x)
    return _upper_gamma_cf(a, x)


def _lower_gamma_series(a: float, x: float) -> float:
    """Regularised lower incomplete gamma P(a, x) via series expansion."""
    ap = a
    total = 1.0 / a
    term = 1.0 / a
    for _ in range(300):
        ap += 1
        term *= x / ap
        total += term
        if abs(term) < abs(total) * 1e-15:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _upper_gamma_cf(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x) via continued fraction."""
    tiny = 1e-30
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 300):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:  # pragma: no cover
            d = tiny
        c = b + an / c
        if abs(c) < tiny:  # pragma: no cover
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h * math.exp(-x + a * math.log(x) - math.lgamma(a))


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="feature",
            type=str,
            required=True,
            description="Feature name to analyse",
        ),
    ],
    responses={200: ExperimentResultsSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_experiment_results(request: Request, environment_api_key: str) -> Response:
    """
    Get experiment results for a feature.

    Returns conversion rates and statistical significance for each variant
    of a feature flag experiment.

    Trait naming convention:
    - Variant tracking: `exp_{feature}_variant` (string value)
    - Conversion tracking: `exp_{feature}_converted` (boolean value)
    """
    query_serializer = ExperimentResultsQuerySerializer(data=request.query_params)
    query_serializer.is_valid(raise_exception=True)

    feature = query_serializer.validated_data["feature"]

    try:
        environment = Environment.objects.get(api_key=environment_api_key)
    except Environment.DoesNotExist:
        return Response(
            {"detail": "Environment not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Check user has permission to view this environment
    # IsAuthenticated ensures user is not AnonymousUser
    if not request.user.has_environment_permission(VIEW_ENVIRONMENT, environment):  # type: ignore[union-attr]
        return Response(
            {"detail": "You do not have permission to view this environment"},
            status=status.HTTP_403_FORBIDDEN,
        )

    variant_trait_key = f"exp_{feature}_variant"
    conversion_trait_key = f"exp_{feature}_converted"

    # Single aggregated query - much faster than N+1 queries
    # Uses indexes on trait_key and identity_id for efficient execution
    variant_stats = (
        Trait.objects.filter(
            identity__environment=environment,
            trait_key=variant_trait_key,
        )
        .exclude(string_value__isnull=True)
        .values("string_value")
        .annotate(
            total=Count("identity", distinct=True),
            conversions=Count(
                "identity",
                distinct=True,
                filter=Q(
                    identity__identity_traits__trait_key=conversion_trait_key,
                    identity__identity_traits__boolean_value=True,
                ),
            ),
        )
    )

    results: dict[str, dict[str, Any]] = {}
    for row in variant_stats:
        variant = row["string_value"]
        total = row["total"]
        conversions = row["conversions"]
        results[variant] = {
            "total": total,
            "conversions": conversions,
            "rate": conversions / total if total > 0 else 0.0,
        }

    # Calculate statistics
    statistics = calculate_statistics(results)

    # Format response
    variant_results = [
        {
            "variant": variant,
            "evaluations": data["total"],
            "conversions": data["conversions"],
            "conversion_rate": round(data["rate"] * 100, 2),
        }
        for variant, data in results.items()
    ]

    response_data = {
        "feature": feature,
        "variants": variant_results,
        "statistics": statistics,
    }

    return Response(response_data)
