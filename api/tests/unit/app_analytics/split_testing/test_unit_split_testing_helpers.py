from app_analytics.split_testing.helpers import analyse_split_test


def test_analyse_split_tests_with_clear_results() -> None:
    # Given
    # Three options, with the last as clear winner as 400 / 500.
    conversion_counts = [100, 200, 400]
    evaluation_counts = [500, 500, 500]

    # When
    pvalue = analyse_split_test(conversion_counts, evaluation_counts)

    # Then
    assert pvalue == 1.473171648576995e-30


def test_analyse_split_tests_with_small_values() -> None:
    # Given
    conversion_counts = [0, 1, 0]
    evaluation_counts = [0, 10, 3]

    # When
    pvalue = analyse_split_test(conversion_counts, evaluation_counts)

    # Then
    assert pvalue == 0.39244638182717423
