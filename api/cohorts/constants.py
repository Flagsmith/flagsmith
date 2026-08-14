COHORT_SYSTEM_TRAIT_KEY_PREFIX = "flagsmith_cohort_"
# Edge identifiers are DynamoDB sort keys, capped at 1024 bytes.
COHORT_IDENTIFIER_MAX_BYTES = 1024
COHORT_MEMBERSHIP_APPLY_BATCH_SIZE = 100
COHORT_MEMBERSHIP_APPLY_MAX_BATCHES_PER_RUN = 10
COHORT_CSV_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
COHORT_CSV_MEMBERSHIP_CREATE_BATCH_SIZE = 1000
DYNAMODB_THROTTLING_ERROR_CODES = frozenset(
    {
        "ProvisionedThroughputExceededException",
        "RequestLimitExceeded",
        "ThrottlingException",
    }
)
