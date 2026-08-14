COHORT_SYSTEM_TRAIT_KEY_PREFIX = "flagsmith_cohort_"
COHORT_MEMBERSHIP_APPLY_BATCH_SIZE = 100
COHORT_MEMBERSHIP_APPLY_MAX_BATCHES_PER_RUN = 10
DYNAMODB_THROTTLING_ERROR_CODES = frozenset(
    {
        "ProvisionedThroughputExceededException",
        "RequestLimitExceeded",
        "ThrottlingException",
    }
)
