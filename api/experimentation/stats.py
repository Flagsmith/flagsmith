import math
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import NormalDist

_STANDARD_NORMAL = NormalDist()
_Z_95 = 1.959963984540054


@dataclass(frozen=True)
class VariantStats:
    n: int
    sum: float
    sum_squares: float

    @property
    def mean(self) -> float:
        return self.sum / self.n

    @property
    def variance(self) -> float:
        return max(0.0, (self.sum_squares - self.sum**2 / self.n) / (self.n - 1))


@dataclass(frozen=True)
class Inference:
    lift: float
    ci_low: float
    ci_high: float
    chance_to_win: float


def compare_to_control(
    control: VariantStats,
    treatment: VariantStats,
) -> Inference | None:
    if control.n < 2 or treatment.n < 2 or control.mean == 0:
        return None

    lift = (treatment.mean - control.mean) / control.mean
    # Delta-method variance of the relative lift; the arms are independent.
    variance = treatment.variance / (
        treatment.n * control.mean**2
    ) + treatment.mean**2 * control.variance / (control.n * control.mean**4)
    standard_error = math.sqrt(variance)
    if standard_error == 0:
        certainty = 0.5 if lift == 0 else float(lift > 0)
        return Inference(lift=lift, ci_low=lift, ci_high=lift, chance_to_win=certainty)

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
    total = sum(observed)
    if len(observed) < 2 or total == 0 or any(s <= 0 for s in expected_shares):
        return None

    statistic = sum(
        (count - total * share) ** 2 / (total * share)
        for count, share in zip(observed, expected_shares, strict=True)
    )
    return _chi_squared_survival(statistic, degrees_of_freedom=len(observed) - 1)


def _chi_squared_survival(statistic: float, degrees_of_freedom: int) -> float:
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
