import numpy as np
from app_analytics.split_testing.helpers import analyse_split_test


def test_analyse_split_tests_with_clear_results() -> None:
    # Given
    # Three options, with the last as clear winner as 400 / 500.
    conversion_counts = [100, 200, 400]
    evaluation_counts = [500, 500, 500]
    input_data = np.array([conversion_counts, evaluation_counts])

    # When
    pvalue, statistic = analyse_split_test(input_data)

    # Then
    assert pvalue == 1.473171648576995e-30
    assert statistic == 137.38027025841336


def test_analyse_split_tests_with_small_values() -> None:
    # Given
    conversion_counts = [0, 1, 0]
    evaluation_counts = [0, 10, 3]
    input_data = np.array([conversion_counts, evaluation_counts])

    # When
    pvalue, statistic = analyse_split_test(input_data)

    # Then
    assert pvalue == 0.39244638182717423
    assert statistic == 1.8707107158019625
