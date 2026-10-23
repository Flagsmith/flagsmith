from rest_framework import status
from rest_framework.exceptions import APIException

from cohorts.constants import COHORT_CSV_MAX_FILE_SIZE_BYTES


class CsvFileTooLargeError(APIException):
    status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    default_detail = (
        "CSV file exceeds the "
        f"{COHORT_CSV_MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB size limit."
    )
    default_code = "csv_file_too_large"
