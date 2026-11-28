import math
import random

import pytest

from features.flag_bisect.engine import (
    Belief,
    Bucket,
    CanaryAdvice,
    Change,
    Cohort,
    Hypothesis,
    conclude,
    design_probe,
    detect_onset,
    involvement,
    judge,
    minutes_to_decide,
    priors,
    recommend_canary,
    sample_ratio_mismatch,
    update,
)

MINUTE = 60_000
ONSET = 1_000 * MINUTE


def _changes(lags_minutes: list[int]) -> list[Change]:
    return [
        Change(key=f"c{i}", changed_at=ONSET - lag * MINUTE)
        for i, lag in enumerate(lags_minutes)
    ]


def _simulate(
    changes: list[Change],
    truth: Hypothesis,
    seed: int,
    fault_rate: float = 0.09,
    baseline_rate: float = 0.01,
    requests: int = 3000,
    canary_share: float = 0.1,
    max_rounds: int = 14,
) -> tuple[str | None, int]:
    rng = random.Random(seed)
    beliefs = priors(changes, ONSET)
    rounds = 0
    for _ in range(max_rounds):
        if conclude(beliefs).status != "undecided":
            break
        design = design_probe(beliefs, [c.key for c in changes])
        assert design is not None
        healed = truth.heals(frozenset(design.revert))
        canary = [0, 0]
        main = [0, 0]
        verdict = "inconclusive"
        for _batch in range(4):
            for _i in range(requests):
                in_canary = rng.random() < canary_share
                rate = baseline_rate if in_canary and healed else fault_rate
                cohort = canary if in_canary else main
                cohort[0] += 1
                cohort[1] += rng.random() < rate
            verdict = judge(
                Cohort(canary[0], canary[1]), Cohort(main[0], main[1]), baseline_rate
            ).verdict
            if verdict != "inconclusive":
                break
        beliefs = update(beliefs, list(design.revert), verdict)  # type: ignore[arg-type]
        rounds += 1
    result = conclude(beliefs)
    return (None if result.status == "undecided" else result.top.key), rounds


def test_detect_onset__step_change__alarms_within_two_minutes_of_the_change() -> None:
    # Given
    rng = random.Random(7)
    buckets = [
        Bucket(
            start=i * MINUTE,
            n=400,
            failures=sum(
                rng.random() < (0.08 if i >= 18 else 0.01) for _ in range(400)
            ),
        )
        for i in range(30)
    ]

    # When
    onset = detect_onset(buckets)

    # Then
    assert onset.alarmed is True
    assert onset.onset_at is not None
    assert abs(onset.onset_at - 18 * MINUTE) <= 2 * MINUTE
    assert 0.005 < onset.baseline_rate < 0.02


def test_detect_onset__stationary_traffic__does_not_alarm() -> None:
    # Given
    rng = random.Random(3)
    buckets = [
        Bucket(i * MINUTE, 400, sum(rng.random() < 0.01 for _ in range(400)))
        for i in range(30)
    ]

    # When
    onset = detect_onset(buckets)

    # Then
    assert onset.alarmed is False
    assert onset.onset_at is None


def test_priors__change_after_onset__weighs_less_than_recent_change_before_it() -> None:
    # Given
    changes = _changes([3, 40, -2])

    # When
    beliefs = {b.hypothesis.key: b.p for b in priors(changes, ONSET)}

    # Then
    assert beliefs["c0"] > beliefs["c1"] > beliefs["c2"]
    assert math.isclose(sum(beliefs.values()), 1.0)
    assert "c0+c1" in beliefs and "none" in beliefs


def test_priors__no_changes__is_certain_nothing_was_changed() -> None:
    # Given / When
    beliefs = priors([], ONSET)

    # Then
    assert [(b.hypothesis.key, b.p) for b in beliefs] == [("none", 1.0)]


def test_design_probe__uniform_single_culprits_without_noise__splits_in_half() -> None:
    # Given
    changes = _changes([5] * 8)
    beliefs = priors(changes, ONSET, none_mass=0.0, pair_mass=0.0)

    # When
    design = design_probe(beliefs, [c.key for c in changes], epsilon=0.0)

    # Then
    assert design is not None
    assert len(design.revert) == 4
    assert math.isclose(design.expected_gain_bits, 1.0)


@pytest.mark.parametrize("enumerate_up_to", [14, 2])
def test_design_probe__max_revert__never_exceeds_the_envelope(
    enumerate_up_to: int,
) -> None:
    # Given
    changes = _changes(list(range(3, 13)))
    beliefs = priors(changes, ONSET)

    # When
    design = design_probe(
        beliefs, [c.key for c in changes], max_revert=2, enumerate_up_to=enumerate_up_to
    )

    # Then
    assert design is not None
    assert 1 <= len(design.revert) <= 2


def test_design_probe__nothing_left_to_learn__returns_none() -> None:
    # Given
    beliefs = [Belief(Hypothesis(("c0",)), 1.0)]

    # When / Then
    assert design_probe(beliefs, ["c0"]) is None
    assert design_probe(beliefs, []) is None


def test_update__healed_then_not_healed__concentrates_on_the_difference() -> None:
    # Given
    changes = _changes([5] * 4)
    beliefs = priors(changes, ONSET, none_mass=0.0, pair_mass=0.0)

    # When
    beliefs = update(beliefs, ["c0", "c1"], "healed", epsilon=0.01)
    beliefs = update(beliefs, ["c0"], "not_healed", epsilon=0.01)

    # Then
    result = conclude(beliefs)
    assert result.top.key == "c1"
    assert result.confidence > 0.97
    assert update(beliefs, ["c1"], "inconclusive") is beliefs


def test_involvement__pair_mass__counts_toward_both_members() -> None:
    # Given
    beliefs = [
        Belief(Hypothesis(("a", "b")), 0.6),
        Belief(Hypothesis(("a",)), 0.4),
    ]

    # When / Then
    assert involvement(beliefs) == {"a": 1.0, "b": 0.6}


@pytest.mark.parametrize(
    "canary, expected",
    [
        (Cohort(400, 6), "healed"),
        (Cohort(1200, 121), "not_healed"),
        (Cohort(400, 80), "harmful"),
        (Cohort(30, 0), "inconclusive"),
        (Cohort(0, 0), "inconclusive"),
        (Cohort(400, 41), "inconclusive"),
    ],
)
def test_judge__canary_outcomes__give_expected_verdicts(
    canary: Cohort, expected: str
) -> None:
    # Given
    main = Cohort(5000, 500)

    # When
    judgement = judge(canary, main, baseline_rate=0.01)

    # Then
    assert judgement.verdict == expected


def test_judge__main_too_small_or_recovered__waits() -> None:
    # Given / When
    small = judge(Cohort(400, 4), Cohort(100, 10), baseline_rate=0.01)
    recovered = judge(Cohort(400, 4), Cohort(5000, 52), baseline_rate=0.01)

    # Then
    assert small.verdict == "inconclusive"
    assert recovered.verdict == "inconclusive"
    assert "no longer visible" in recovered.reason


def test_judge__healed__reports_recovered_fraction_and_interval() -> None:
    # Given / When
    judgement = judge(Cohort(600, 6), Cohort(6000, 540), baseline_rate=0.01)

    # Then
    assert judgement.verdict == "healed"
    assert 0.85 < judgement.recovered < 1.1
    assert judgement.ci_low > 0
    assert judgement.evidence >= 20


def test_sample_ratio_mismatch__share_far_from_configured__is_flagged() -> None:
    # Given a 10% canary share
    expected_share = 0.1

    # When
    on_target = sample_ratio_mismatch(1000, 10000, expected_share)
    far_off = sample_ratio_mismatch(1400, 10000, expected_share)
    no_traffic = sample_ratio_mismatch(0, 0, expected_share)

    # Then
    assert (on_target, far_off, no_traffic) == (False, True, False)


def test_bisection__single_culprit_over_30_seeds__is_found_in_few_rounds() -> None:
    # Given
    found = 0
    worst = 0
    for seed in range(1, 31):
        changes = _changes([4 + ((i * 7 + seed) % 11) for i in range(8)])
        truth = Hypothesis((f"c{seed % 8}",))

        # When
        key, rounds = _simulate(changes, truth, seed)

        # Then
        found += key == truth.key
        worst = max(worst, rounds)
    assert found >= 29
    assert worst <= 10


def test_bisection__pair_interaction__names_both_changes() -> None:
    # Given
    changes = _changes([4, 5, 6, 7, 8, 9])
    truth = Hypothesis(("c1", "c4"))

    # When
    key, _ = _simulate(changes, truth, seed=3, fault_rate=0.1, requests=4000)

    # Then
    assert key == "c1+c4"


def test_bisection__regression_from_elsewhere__concludes_not_a_flag_change() -> None:
    # Given
    changes = _changes([4, 5, 6, 7, 8])

    # When
    key, _ = _simulate(changes, Hypothesis(()), seed=11)

    # Then
    assert key == "none"


@pytest.mark.parametrize(
    "per_minute, canary_share, expected",
    [
        (1400, 0.10, 4.5),
        (1400, 0.20, 2.5),
        (600, 0.05, None),
    ],
)
def test_minutes_to_decide__expected_outcomes__returns_slower_of_both_verdicts(
    per_minute: float, canary_share: float, expected: float | None
) -> None:
    # Given / When
    minutes = minutes_to_decide(per_minute, canary_share, 0.01, 0.09)

    # Then
    assert minutes == expected


@pytest.mark.parametrize(
    "per_minute, regression_rate, expected",
    [
        # Enough traffic: the smallest canary that decides within five minutes.
        (1400, 0.09, CanaryAdvice(10, 4.5)),
        # The largest canary is still slower than the target: say how slow.
        (600, 0.09, CanaryAdvice(20, 5.5)),
        # Too little traffic for this regression at any size.
        (600, 0.04, CanaryAdvice(20, None)),
    ],
)
def test_recommend_canary__traffic_and_regression__sizes_the_canary(
    per_minute: float, regression_rate: float, expected: CanaryAdvice
) -> None:
    # Given / When
    advice = recommend_canary(per_minute, 0.01, regression_rate)

    # Then
    assert advice == expected
