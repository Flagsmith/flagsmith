"""Bayesian statistics for experiment results.

Compares a treatment variant against control and reports, in plain terms:
how much better/worse the treatment did (``lift``), how sure we are
(``chance_to_win`` and the credible interval), and whether traffic was split
fairly between variants (``srm_p_value``). All inputs are summary numbers; no
raw events reach this module.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist

_STANDARD_NORMAL = NormalDist()
# A 95% interval spans the mean ± 1.96 standard deviations of a normal curve.
_Z_95 = 1.959963984540054


@dataclass(frozen=True)
class VariantStats:
    """Everything we need to know about one variant, as three running totals.

    For a conversion metric each identity contributes 0 or 1, so ``sum`` is the
    conversion count; for a value metric (e.g. revenue) it is the total. These
    three numbers are enough to recover the average and the spread, so the
    warehouse never has to send per-identity rows.
    """

    n: int  # identities in the variant
    sum: float  # total of their per-identity values
    sum_squares: float  # total of the squares, used to derive the spread

    @property
    def mean(self) -> float:
        return self.sum / self.n

    @property
    def variance(self) -> float:
        # Spread of the per-identity values. max(0, …) guards against tiny
        # negative results from floating-point error when every value is equal.
        return max(0.0, (self.sum_squares - self.sum**2 / self.n) / (self.n - 1))


@dataclass(frozen=True)
class Inference:
    lift: float  # relative change vs control, e.g. 0.12 == +12%
    ci_low: float  # credible interval: we're 95% sure the true lift
    ci_high: float  # lies between ci_low and ci_high
    chance_to_win: float  # probability (0–1) the treatment really beats control


def compare_to_control(
    control: VariantStats,
    treatment: VariantStats,
) -> Inference | None:
    # Inference is undefined without two observations per arm (no spread to
    # measure) or a non-positive control mean (relative lift against it is
    # meaningless, and divides by zero when the mean is exactly zero).
    if control.n < 2 or treatment.n < 2 or control.mean <= 0:
        return None

    lift = (treatment.mean - control.mean) / control.mean
    # How uncertain that lift is. Both arms are noisy, so the uncertainty of a
    # ratio combines both; the delta method is the standard approximation, and
    # the arms being independent means there is no covariance term.
    variance = treatment.variance / (
        treatment.n * control.mean**2
    ) + treatment.mean**2 * control.variance / (control.n * control.mean**4)
    standard_error = math.sqrt(variance)
    if standard_error == 0:
        # No uncertainty (every value identical): the result is exact.
        certainty = 0.5 if lift == 0 else float(lift > 0)
        return Inference(lift=lift, ci_low=lift, ci_high=lift, chance_to_win=certainty)

    # Treat the true lift as a normal curve centred on `lift`, `standard_error`
    # wide. The interval is its middle 95%; chance_to_win is the share of the
    # curve above zero (i.e. how much of our belief says the treatment is up).
    return Inference(
        lift=lift,
        ci_low=lift - _Z_95 * standard_error,
        ci_high=lift + _Z_95 * standard_error,
        chance_to_win=_STANDARD_NORMAL.cdf(lift / standard_error),
    )


def srm_p_value(
    observed: Sequence[int],
    expected_shares: Sequence[float],
) -> float | None:
    """Sample ratio mismatch check: was traffic split as configured?

    Returns the probability that random assignment alone would drift from the
    configured split at least as much as we observed. A tiny value (< 0.001 by
    convention) means the split is broken and the results can't be trusted.
    ``None`` when the question is meaningless (no traffic, one variant).
    """
    total = sum(observed)
    if len(observed) < 2 or total == 0 or any(s <= 0 for s in expected_shares):
        return None

    # Chi-squared statistic: total squared gap between observed and expected
    # counts, scaled by what's expected. Bigger gap == bigger number.
    statistic = sum(
        (count - total * share) ** 2 / (total * share)
        for count, share in zip(observed, expected_shares, strict=True)
    )
    return _chi_squared_survival(statistic, degrees_of_freedom=len(observed) - 1)


def _chi_squared_survival(statistic: float, degrees_of_freedom: int) -> float:
    # Turns the chi-squared statistic into a probability (the p-value above):
    # how likely a gap this large is by chance. 0 gap → certain (1.0).
    if statistic <= 0:
        return 1.0
    # The standard library has no chi-squared distribution, but for integer
    # degrees of freedom the survival function is exact from the base cases
    # Q(1/2, y) = erfc(√y) and Q(1, y) = e⁻ʸ via the recurrence
    # Q(a+1, y) = Q(a, y) + yᵃe⁻ʸ/Γ(a+1).
    y = statistic / 2.0
    if degrees_of_freedom % 2:
        a = 0.5
        survival = math.erfc(math.sqrt(y))
    else:
        a = 1.0
        survival = math.exp(-y)
    while a + 1.0 <= degrees_of_freedom / 2.0:
        survival += math.exp(a * math.log(y) - y - math.lgamma(a + 1.0))
        a += 1.0
    return survival
