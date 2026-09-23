import pytest

from experimentation.stats import (
    Inference,
    VariantStats,
    compare_to_control,
    srm_p_value,
)


def test_variant_stats__sufficient_statistics__derive_mean_and_variance() -> None:
    # Given 1000 identities with 100 conversions (0/1 values)
    stats = VariantStats(n=1000, sum=100.0, sum_squares=100.0)

    # When / Then
    assert stats.mean == 0.1
    assert stats.variance == pytest.approx(90.0 / 999.0)


def test_variant_stats__float_noise__variance_clamped_to_zero() -> None:
    # Given sums whose rounding puts the raw variance just below zero
    stats = VariantStats(n=2, sum=2.0, sum_squares=1.9999999999999996)

    # When / Then
    assert stats.variance == 0.0


def test_compare_to_control__more_conversions__positive_lift_inference() -> None:
    # Given a 10% control and a 12% treatment, 1000 identities each
    control = VariantStats(n=1000, sum=100.0, sum_squares=100.0)
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)

    # When
    inference = compare_to_control(control, treatment)

    # Then
    assert inference is not None
    assert inference.lift == pytest.approx(0.2)
    assert inference.ci_low == pytest.approx(-0.10074, abs=1e-4)
    assert inference.ci_high == pytest.approx(0.50074, abs=1e-4)
    assert inference.chance_to_win == pytest.approx(0.90379, abs=1e-4)


def test_compare_to_control__identical_arms__chance_is_even() -> None:
    # Given two arms with the same conversions
    arm = VariantStats(n=1000, sum=100.0, sum_squares=100.0)

    # When
    inference = compare_to_control(arm, arm)

    # Then
    assert inference is not None
    assert inference.lift == 0.0
    assert inference.chance_to_win == 0.5
    assert inference.ci_low == pytest.approx(-inference.ci_high)


@pytest.mark.parametrize(
    "treatment, expected",
    [
        (
            VariantStats(n=10, sum=20.0, sum_squares=40.0),
            Inference(lift=1.0, ci_low=1.0, ci_high=1.0, chance_to_win=1.0),
        ),
        (
            VariantStats(n=10, sum=5.0, sum_squares=2.5),
            Inference(lift=-0.5, ci_low=-0.5, ci_high=-0.5, chance_to_win=0.0),
        ),
        (
            VariantStats(n=10, sum=10.0, sum_squares=10.0),
            Inference(lift=0.0, ci_low=0.0, ci_high=0.0, chance_to_win=0.5),
        ),
    ],
    ids=["better", "worse", "equal"],
)
def test_compare_to_control__zero_variance_arms__degenerate_certainty(
    treatment: VariantStats,
    expected: Inference,
) -> None:
    # Given arms with constant values (zero variance)
    control = VariantStats(n=10, sum=10.0, sum_squares=10.0)

    # When / Then
    assert compare_to_control(control, treatment) == expected


def test_compare_to_control__zero_control_mean__returns_none() -> None:
    # Given a control with no conversions: relative lift is undefined
    control = VariantStats(n=1000, sum=0.0, sum_squares=0.0)
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)

    # When / Then
    assert compare_to_control(control, treatment) is None


def test_compare_to_control__negative_control_mean__returns_none() -> None:
    # Given a control whose values average below zero (e.g. a revenue metric
    # with refunds): relative lift against it is meaningless
    control = VariantStats(n=1000, sum=-50.0, sum_squares=600.0)
    treatment = VariantStats(n=1000, sum=120.0, sum_squares=120.0)

    # When / Then
    assert compare_to_control(control, treatment) is None


@pytest.mark.parametrize(
    "control_n, treatment_n",
    [(1, 1000), (1000, 1), (0, 1000)],
    ids=["control_too_small", "treatment_too_small", "control_empty"],
)
def test_compare_to_control__insufficient_observations__returns_none(
    control_n: int,
    treatment_n: int,
) -> None:
    # Given an arm with fewer than two observations: variance is undefined
    control = VariantStats(
        n=control_n, sum=float(control_n), sum_squares=float(control_n)
    )
    treatment = VariantStats(
        n=treatment_n, sum=float(treatment_n), sum_squares=float(treatment_n)
    )

    # When / Then
    assert compare_to_control(control, treatment) is None


def test_srm_p_value__balanced_split__no_mismatch() -> None:
    # Given observed counts exactly matching the expected 50/50 split
    # When
    p_value = srm_p_value([5000, 5000], [0.5, 0.5])

    # Then
    assert p_value == pytest.approx(1.0)


@pytest.mark.parametrize(
    "observed, shares, expected_p",
    [
        # chi-squared = 4.0, 1 dof
        ([5100, 4900], [0.5, 0.5], 0.04550),
        # chi-squared = 2.0, 2 dof: survival is exp(-1)
        ([3400, 3300, 3300], [1 / 3, 1 / 3, 1 / 3], 0.36788),
        # chi-squared = 8.0, 3 dof
        ([2600, 2500, 2500, 2400], [0.25, 0.25, 0.25, 0.25], 0.04601),
    ],
    ids=["one_dof", "two_dof", "three_dof"],
)
def test_srm_p_value__known_chi_squared__matches_reference(
    observed: list[int],
    shares: list[float],
    expected_p: float,
) -> None:
    # Given observed counts with a hand-computed chi-squared statistic
    # When / Then
    assert srm_p_value(observed, shares) == pytest.approx(expected_p, abs=1e-4)


def test_srm_p_value__heavy_imbalance__fails_threshold() -> None:
    # Given a 60/40 observed split against an expected 50/50
    # When
    p_value = srm_p_value([6000, 4000], [0.5, 0.5])

    # Then
    assert p_value is not None
    assert p_value < 0.001


@pytest.mark.parametrize(
    "observed, shares",
    [
        ([0, 0], [0.5, 0.5]),
        ([5000, 5000], [1.0, 0.0]),
        ([10000], [1.0]),
    ],
    ids=["no_observations", "zero_share", "single_variant"],
)
def test_srm_p_value__not_computable__returns_none(
    observed: list[int],
    shares: list[float],
) -> None:
    # Given inputs the chi-squared test is undefined for
    # When / Then
    assert srm_p_value(observed, shares) is None
