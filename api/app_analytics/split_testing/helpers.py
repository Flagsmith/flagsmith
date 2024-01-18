import numpy as np
from scipy.stats import chi2_contingency


def analyse_split_test(
    conversion_counts: list[int], evaluation_counts: list[int]
) -> float:
    """
    Analyse conversion and evaluation counts against the chisquared
    contingency test with correction enabled and with the important
    log-likelihood argument set in order to accomplish what is
    more commonly known as the G-Test with the p-value returned.
    The p-value is a measure indicating the strength of evidence
    against a null hypothesis with smaller values indicating more
    statistical strength in the relationship being non-random.
    """
    # Reform input data to scipy's format.
    observed_matrix = np.array([conversion_counts, evaluation_counts])

    # Replace zero values in order for the chi-squared results to
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

    # Typically a pvalue of around 1% or lower is ideal, though
    # as large as 5% is acceptable for some tests.
    return results.pvalue


def gather_split_test_metrics(
    evaluation_counts: dict[int, int], conversion_counts: dict[int, int]
) -> float:
    """
    Take in evalaution counts (aka, views of the individual features) and
    match them up against the conversion counts in order to run the
    split test analysis function above.
    """
    _evaluation_counts = []
    _conversion_counts = []
    for mv_feature_option_id, evaluation_count in evaluation_counts.items():
        _evaluation_counts.append(evaluation_count)
        _conversion_counts.append(conversion_counts[mv_feature_option_id])

    return analyse_split_test(_conversion_counts, _evaluation_counts)
