import random

from rest_framework import status
from rest_framework.test import APIClient

from app_analytics.experiments import calculate_statistics
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment


def test_calculate_statistics__two_variants__returns_correct_stats() -> None:
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 1000, "conversions": 100, "rate": 0.10},
        "green": {"total": 1000, "conversions": 150, "rate": 0.15},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is True
    assert stats["p_value"] < 0.05
    assert stats["winner"] == "green"
    assert stats["chance_to_win"]["green"] > 0.9
    assert "+50" in stats["lift"] or "+49" in stats["lift"]


def test_calculate_statistics__not_significant__returns_no_winner() -> None:
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 100, "conversions": 10, "rate": 0.10},
        "green": {"total": 100, "conversions": 11, "rate": 0.11},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert stats["winner"] is None
    assert "Keep collecting data" in stats["recommendation"]


def test_calculate_statistics__no_variants__returns_no_data_message() -> None:
    # Given
    results: dict[str, dict[str, object]] = {}

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert stats["p_value"] == 1.0
    assert stats["recommendation"] == "No experiment data found"


def test_calculate_statistics__zero_conversions__returns_not_significant() -> None:
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 500, "conversions": 0, "rate": 0.0},
        "green": {"total": 500, "conversions": 0, "rate": 0.0},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert stats["p_value"] == 1.0


def test_calculate_statistics__equal_rates__returns_not_significant() -> None:
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 500, "conversions": 50, "rate": 0.10},
        "green": {"total": 500, "conversions": 50, "rate": 0.10},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert stats["winner"] is None


def test_calculate_statistics__two_variants_first_wins__returns_correct_winner() -> (
    None
):
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 1000, "conversions": 150, "rate": 0.15},
        "green": {"total": 1000, "conversions": 100, "rate": 0.10},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["winner"] == "blue"


def test_calculate_statistics__moderate_sample__returns_sample_warning() -> None:
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 50, "conversions": 5, "rate": 0.10},
        "green": {"total": 50, "conversions": 15, "rate": 0.30},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["sample_size_warning"] is not None
    assert "modest" in stats["sample_size_warning"]


def test_calculate_statistics__zero_total_variant__returns_insufficient_data() -> None:
    # Given
    results = {
        "blue": {"total": 100, "conversions": 10, "rate": 0.10},
        "green": {"total": 0, "conversions": 0, "rate": 0.0},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert "Insufficient data" in stats["recommendation"]


def test_calculate_statistics__multi_variant_zero_total__returns_insufficient_data() -> (
    None
):
    # Given
    results = {
        "blue": {"total": 100, "conversions": 10, "rate": 0.10},
        "green": {"total": 100, "conversions": 15, "rate": 0.15},
        "red": {"total": 0, "conversions": 0, "rate": 0.0},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert "Insufficient data" in stats["recommendation"]


def test_calculate_statistics__small_sample__uses_series_expansion() -> None:
    # Given - small G-statistic triggers series path (x < a+1)
    random.seed(42)
    results = {
        "blue": {"total": 20, "conversions": 2, "rate": 0.10},
        "green": {"total": 20, "conversions": 3, "rate": 0.15},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert stats["significant"] is False
    assert 0.0 <= stats["p_value"] <= 1.0
    assert stats["sample_size_warning"] is not None


def test_calculate_statistics__single_variant__returns_error_message() -> None:
    # Given
    results = {
        "blue": {"total": 1000, "conversions": 100, "rate": 0.10},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert "Need at least 2 variants" in stats["recommendation"]


def test_calculate_statistics__three_variants__returns_stats_for_all() -> None:
    # Given
    random.seed(42)
    results = {
        "blue": {"total": 1000, "conversions": 100, "rate": 0.10},
        "green": {"total": 1000, "conversions": 150, "rate": 0.15},
        "red": {"total": 1000, "conversions": 120, "rate": 0.12},
    }

    # When
    stats = calculate_statistics(results)

    # Then
    assert "blue" in stats["chance_to_win"]
    assert "green" in stats["chance_to_win"]
    assert "red" in stats["chance_to_win"]
    assert stats["chance_to_win"]["green"] > stats["chance_to_win"]["blue"]


def test_get_experiment_results__with_data__returns_results(
    environment: Environment,
    admin_client_original: APIClient,
) -> None:
    # Given
    feature_name = "checkout_button"

    for i in range(50):
        identity = Identity.objects.create(
            identifier=f"user_{i}",
            environment=environment,
        )
        variant = "blue" if i < 25 else "green"
        Trait.objects.create(
            identity=identity,
            trait_key=f"exp_{feature_name}_variant",
            string_value=variant,
            value_type="unicode",
        )
        if (variant == "blue" and i % 5 == 0) or (variant == "green" and i % 3 == 0):
            Trait.objects.create(
                identity=identity,
                trait_key=f"exp_{feature_name}_converted",
                boolean_value=True,
                value_type="bool",
            )

    url = f"/api/v1/environments/{environment.api_key}/experiments/results/"

    # When
    response = admin_client_original.get(url, {"feature": feature_name})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["feature"] == feature_name
    assert len(data["variants"]) == 2
    assert "statistics" in data
    assert "p_value" in data["statistics"]
    assert "chance_to_win" in data["statistics"]


def test_get_experiment_results__no_data__returns_empty_results(
    environment: Environment,
    admin_client_original: APIClient,
) -> None:
    # Given
    url = f"/api/v1/environments/{environment.api_key}/experiments/results/"

    # When
    response = admin_client_original.get(url, {"feature": "nonexistent_feature"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["variants"] == []


def test_get_experiment_results__missing_feature_param__returns_400(
    environment: Environment,
    admin_client_original: APIClient,
) -> None:
    # Given
    url = f"/api/v1/environments/{environment.api_key}/experiments/results/"

    # When
    response = admin_client_original.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
