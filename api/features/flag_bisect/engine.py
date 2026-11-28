"""Statistics for Flag Bisect. Pure functions, no Django, deterministic.

- Onset: Bernoulli CUSUM (Page 1954) over per-minute failure counts.
- Culprit search: Bayesian noisy group testing over "none of these changes", each
  single change, and each pair of changes that only fails together. A probe
  reverts a set R of changes for a canary segment; under a single change i the
  canary heals iff i is in R, under a pair (i, j) iff i or j is in R, under "none"
  never. The next R maximises expected information gain (noisy bisection, as in
  Horstein; Waeber, Frazier and Henderson 2013; Google's flake-aware culprit
  finding, ICST 2023).
- Per probe: plug-in two-sample mixture SPRT (Johari, Pekelis and Walsh,
  "Always valid inference", arXiv:1512.04922). Validity is asymptotic.
"""

import math
from dataclasses import dataclass, field
from itertools import combinations
from typing import Literal

Verdict = Literal["healed", "not_healed", "inconclusive", "harmful"]

NONE_KEY = "none"


@dataclass(frozen=True)
class Bucket:
    start: int
    n: int
    failures: int


@dataclass(frozen=True)
class Onset:
    alarmed: bool
    onset_at: int | None
    alarm_at: int | None
    baseline_rate: float


def detect_onset(
    buckets: list[Bucket],
    baseline_buckets: int = 5,
    shift_ratio: float = 2.0,
    min_shift: float = 0.02,
    threshold: float = 8.0,
) -> Onset:
    """Bernoulli CUSUM: S_t = max(0, S_{t-1} + LLR_t); alarm when S_t > threshold.

    The baseline rate comes from the first `baseline_buckets` buckets; the onset is
    the bucket after the last time the statistic was zero before the alarm.
    """
    k = max(1, min(baseline_buckets, len(buckets)))
    base_n = sum(b.n for b in buckets[:k])
    base_f = sum(b.failures for b in buckets[:k])
    p0 = min(0.5, max(1e-4, (base_f + 0.5) / (base_n + 1)))
    p1 = min(0.99, max(p0 * shift_ratio, p0 + min_shift))
    log_fail = math.log(p1 / p0)
    log_ok = math.log((1 - p1) / (1 - p0))
    statistic = 0.0
    last_zero = k - 1
    for i in range(k, len(buckets)):
        b = buckets[i]
        statistic = max(
            0.0, statistic + b.failures * log_fail + (b.n - b.failures) * log_ok
        )
        if statistic == 0.0:
            last_zero = i
        if statistic > threshold:
            onset_index = min(len(buckets) - 1, last_zero + 1)
            return Onset(True, buckets[onset_index].start, b.start, p0)
    return Onset(False, None, None, p0)


@dataclass(frozen=True)
class Change:
    """A recent change to one flag; `changed_at` in epoch milliseconds."""

    key: str
    changed_at: int
    blast_radius: float = 1.0


@dataclass(frozen=True)
class Hypothesis:
    """No culprit (empty), one change, or a pair that only fails together."""

    ids: tuple[str, ...]

    @property
    def key(self) -> str:
        return "+".join(self.ids) if self.ids else NONE_KEY

    def heals(self, revert: frozenset[str]) -> bool:
        return any(i in revert for i in self.ids)


@dataclass
class Belief:
    hypothesis: Hypothesis
    p: float


def _normalise(beliefs: list[Belief]) -> list[Belief]:
    total = sum(b.p for b in beliefs)
    if total <= 0:
        return beliefs
    return [Belief(b.hypothesis, b.p / total) for b in beliefs]


def priors(
    changes: list[Change],
    onset_ms: int,
    none_mass: float = 0.08,
    pair_mass: float = 0.12,
    recency_tau_ms: int = 20 * 60_000,
) -> list[Belief]:
    """Prior odds: recent changes before the onset weigh more; later ones little."""
    if not changes:
        return [Belief(Hypothesis(()), 1.0)]
    pairs_mass = pair_mass if len(changes) > 1 else 0.0
    weights: dict[str, float] = {}
    for c in changes:
        lag = onset_ms - c.changed_at
        recency = 0.03 if lag < 0 else math.exp(-lag / recency_tau_ms)
        blast = 0.5 + 0.5 * min(1.0, max(0.0, c.blast_radius))
        weights[c.key] = max(1e-6, recency * blast)
    total = sum(weights.values())
    single = {k: w / total for k, w in weights.items()}
    beliefs = [Belief(Hypothesis(()), none_mass)]
    beliefs += [
        Belief(Hypothesis((c.key,)), (1 - none_mass - pairs_mass) * single[c.key])
        for c in changes
    ]
    if pairs_mass > 0:
        pairs = [
            (tuple(sorted((a.key, b.key))), math.sqrt(single[a.key] * single[b.key]))
            for a, b in combinations(changes, 2)
        ]
        pair_total = sum(w for _, w in pairs)
        beliefs += [
            Belief(Hypothesis(ids), pairs_mass * w / pair_total) for ids, w in pairs
        ]
    return _normalise(beliefs)


def update(
    beliefs: list[Belief], revert: list[str], verdict: Verdict, epsilon: float = 0.05
) -> list[Belief]:
    """Bayes' rule with a noisy channel. Inconclusive or harmful leave odds as they are."""
    if verdict not in ("healed", "not_healed"):
        return beliefs
    r = frozenset(revert)
    out = []
    for b in beliefs:
        heals = b.hypothesis.heals(r)
        if verdict == "healed":
            likelihood = 1 - epsilon if heals else epsilon
        else:
            likelihood = epsilon if heals else 1 - epsilon
        out.append(Belief(b.hypothesis, b.p * likelihood))
    return _normalise(out)


def _h2(p: float) -> float:
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def expected_gain(
    beliefs: list[Belief], revert: frozenset[str], epsilon: float
) -> tuple[float, float]:
    """(mutual information in bits, posterior mass that would heal) for reverting `revert`."""
    heal_mass = sum(b.p for b in beliefs if b.hypothesis.heals(revert))
    p_healed = heal_mass * (1 - epsilon) + (1 - heal_mass) * epsilon
    return _h2(p_healed) - _h2(epsilon), heal_mass


@dataclass(frozen=True)
class ProbeDesign:
    revert: tuple[str, ...]
    expected_gain_bits: float
    heal_mass: float


def _greedy_candidate(
    beliefs: list[Belief], ids: list[str], limit: int, epsilon: float
) -> tuple[str, ...]:
    """Adds the change that raises the expected gain most, while it does."""
    chosen: list[str] = []
    current = 0.0
    while len(chosen) < limit:
        options = [
            (expected_gain(beliefs, frozenset([*chosen, i]), epsilon)[0], i)
            for i in ids
            if i not in chosen
        ]
        gain, pick = sorted(options, key=lambda o: (-o[0], o[1]))[0]
        if gain <= current + 1e-12:
            break
        chosen.append(pick)
        current = gain
    return tuple(sorted(chosen))


def _candidates(
    beliefs: list[Belief],
    ids: list[str],
    limit: int,
    epsilon: float,
    enumerate_up_to: int,
) -> list[tuple[str, ...]]:
    if len(ids) <= enumerate_up_to:
        return [
            candidate
            for size in range(1, limit + 1)
            for candidate in combinations(ids, size)
        ]
    greedy = _greedy_candidate(beliefs, ids, limit, epsilon)
    return [greedy] if greedy else []


def design_probe(
    beliefs: list[Belief],
    keys: list[str],
    max_revert: int | None = None,
    epsilon: float = 0.05,
    enumerate_up_to: int = 14,
) -> ProbeDesign | None:
    """The set of changes to revert next. Exhaustive up to `enumerate_up_to` keys, greedy above.

    Ties go to the smaller set, then to lexicographic order, so the choice is deterministic.
    """
    ids = sorted(keys)
    if not ids:
        return None
    limit = max(1, min(max_revert or len(ids), len(ids)))
    scored = [
        (*expected_gain(beliefs, frozenset(c), epsilon), c)
        for c in _candidates(beliefs, ids, limit, epsilon, enumerate_up_to)
    ]
    if not scored:
        return None
    gain, heal, chosen = sorted(
        scored, key=lambda s: (-round(s[0], 12), len(s[2]), s[2])
    )[0]
    if gain <= 1e-9:
        return None
    return ProbeDesign(chosen, gain, heal)


@dataclass(frozen=True)
class Conclusion:
    status: Literal["identified", "not_a_flag_change", "undecided"]
    top: Hypothesis
    confidence: float


def conclude(beliefs: list[Belief], threshold: float = 0.95) -> Conclusion:
    top = sorted(beliefs, key=lambda b: (-b.p, b.hypothesis.key))[0]
    if top.p >= threshold:
        status: Literal["identified", "not_a_flag_change"] = (
            "identified" if top.hypothesis.ids else "not_a_flag_change"
        )
        return Conclusion(status, top.hypothesis, top.p)
    return Conclusion("undecided", top.hypothesis, top.p)


def involvement(beliefs: list[Belief]) -> dict[str, float]:
    """Marginal probability that each change is involved, alone or as half of a pair."""
    out: dict[str, float] = {}
    for b in beliefs:
        for i in b.hypothesis.ids:
            out[i] = out.get(i, 0.0) + b.p
    return out


@dataclass(frozen=True)
class Cohort:
    n: int
    failures: int

    @property
    def rate(self) -> float:
        return self.failures / self.n if self.n else 0.0


@dataclass(frozen=True)
class Judgement:
    verdict: Verdict
    canary_rate: float
    main_rate: float
    baseline_rate: float
    theta: float
    delta: float
    ci_low: float
    ci_high: float
    evidence: float
    recovered: float
    reason: str
    extra: dict[str, float] = field(default_factory=dict)


def judge(
    canary: Cohort,
    main: Cohort,
    baseline_rate: float,
    alpha: float = 0.05,
    rho: float = 0.5,
    min_samples: int = 150,
    harm_margin: float = 0.02,
    min_effect: float = 0.01,
) -> Judgement:
    """Two-sample mSPRT on theta = p_main - p_canary with tau = delta = p_main - p_baseline.

    healed: evidence >= 1/alpha and theta > 0. not_healed: theta + h < rho * delta.
    harmful: theta + h < -harm_margin. Otherwise inconclusive.
    """
    eps = 1e-6
    delta = main.rate - baseline_rate
    theta = main.rate - canary.rate
    recovered = theta / delta if delta > 0 else 0.0

    def result(
        verdict: Verdict,
        reason: str,
        ci: tuple[float, float] = (-1.0, 1.0),
        ev: float = 0.0,
    ) -> Judgement:
        return Judgement(
            verdict,
            canary.rate,
            main.rate,
            baseline_rate,
            theta,
            delta,
            ci[0],
            ci[1],
            ev,
            recovered,
            reason,
        )

    if main.n < min_samples:
        return result(
            "inconclusive", f"main population has {main.n} of {min_samples} samples"
        )
    if delta < min_effect:
        return result(
            "inconclusive", "the regression is no longer visible in the main population"
        )
    if canary.n == 0:
        return result("inconclusive", "no canary traffic yet")
    pc = min(1 - eps, max(eps, canary.rate))
    pm = min(1 - eps, max(eps, main.rate))
    variance = pc * (1 - pc) / canary.n + pm * (1 - pm) / main.n
    tau2 = delta * delta
    exponent = tau2 * theta * theta / (2 * variance * (variance + tau2))
    evidence = math.sqrt(variance / (variance + tau2)) * math.exp(min(exponent, 700.0))
    half = math.sqrt(
        variance
        * (variance + tau2)
        / tau2
        * (2 * math.log(1 / alpha) + math.log((variance + tau2) / variance))
    )
    ci = (theta - half, theta + half)
    if theta + half < -harm_margin:
        return result(
            "harmful", "the canary is worse than the main population", ci, evidence
        )
    if canary.n < min_samples:
        return result(
            "inconclusive",
            f"canary has {canary.n} of {min_samples} samples",
            ci,
            evidence,
        )
    if evidence >= 1 / alpha and theta > 0:
        return result(
            "healed",
            f"reverting removes {round(recovered * 100)}% of the regression",
            ci,
            evidence,
        )
    if theta + half < rho * delta:
        return result(
            "not_healed",
            f"reverting removes less than {round(rho * 100)}% of the regression",
            ci,
            evidence,
        )
    return result("inconclusive", "not decisive yet", ci, evidence)


def sample_ratio_mismatch(canary_n: int, total_n: int, expected_share: float) -> bool:
    """Chi-square goodness of fit, one degree of freedom, p < 0.001."""
    if total_n == 0 or not 0 < expected_share < 1:
        return False
    expected_canary = total_n * expected_share
    expected_main = total_n - expected_canary
    chi2 = (canary_n - expected_canary) ** 2 / expected_canary + (
        (total_n - canary_n) - expected_main
    ) ** 2 / expected_main
    return chi2 > 10.83


def minutes_to_decide(
    per_minute: float,
    canary_share: float,
    baseline_rate: float,
    regression_rate: float,
    step_minutes: float = 0.5,
    limit_minutes: float = 12.0,
) -> float | None:
    """Minutes until the Judge decides a probe, if outcomes arrive at their expected rates.

    Takes the slower of the two answers a probe can give: healed (it reverted the
    culprit) and not healed (it did not). None if neither is reached within the limit.
    """

    def first_decision(canary_rate: float, wanted: Verdict) -> float | None:
        minutes = 0.0
        while minutes < limit_minutes:
            minutes += step_minutes
            total = per_minute * minutes
            canary_n = round(total * canary_share)
            main_n = round(total) - canary_n
            verdict = judge(
                Cohort(canary_n, round(canary_n * canary_rate)),
                Cohort(main_n, round(main_n * regression_rate)),
                baseline_rate,
            ).verdict
            if verdict == wanted:
                return minutes
        return None

    healed = first_decision(baseline_rate, "healed")
    not_healed = first_decision(regression_rate, "not_healed")
    if healed is None or not_healed is None:
        return None
    return max(healed, not_healed)


@dataclass(frozen=True)
class CanaryAdvice:
    percent: int
    minutes: float | None  # expected minutes per probe; None if beyond the limit


def recommend_canary(
    per_minute: float,
    baseline_rate: float,
    regression_rate: float,
    choices: tuple[int, ...] = (5, 10, 15, 20),
    target_minutes: float = 5.0,
) -> CanaryAdvice:
    """The smallest canary whose probes should decide within `target_minutes`.

    The largest choice when none does, with its expected minutes (or None) so a
    person can see before approving that probes will be slow or undecided.
    """
    minutes: float | None = None
    for percent in choices:
        minutes = minutes_to_decide(
            per_minute, percent / 100, baseline_rate, regression_rate
        )
        if minutes is not None and minutes <= target_minutes:
            return CanaryAdvice(percent, minutes)
    return CanaryAdvice(choices[-1], minutes)
