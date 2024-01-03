import numpy as np
from scipy.stats import chi2_contingency


def analyse_split_test(observed_matrix: np.array) -> tuple[float, float]:
    # Replace zero values in order for the chi-squared results can
    # be fully calculated. Don't worry about false results since
    # the pvalue will be much too low to matter to the user.
    replacement_value = 1
    observed_matrix = np.where(observed_matrix == 0, replacement_value, observed_matrix)

    # Calculate the results with correction set to `True` and the
    # lambda set to what is commonly known as the G-Test.
    results = chi2_contingency(
        observed_matrix,
        correction=True,
        lambda_="log-likelihood",
    )

    # Return the most important result, the pvalue, as well as a
    # possibly useful statistic addition for the frontend.
    # Typically a pvalue of around 1% is ideal, though as large
    # as 5% is acceptable for some tests.
    return results.pvalue, results.statistic


def gather_split_test_metrics(
    evaluation_counts: dict[int, int], conversion_counts: dict[int, int]
) -> tuple[float, float]:
    _evaluation_counts = []
    _conversion_counts = []
    for mv_feature_option_id, evaluation_count in evaluation_counts.items():
        _evaluation_counts.append(evaluation_count)
        _conversion_counts.append(conversion_counts[mv_feature_option_id])
    input_data = np.array([_conversion_counts, _evaluation_counts])
    return analyse_split_test(input_data)
