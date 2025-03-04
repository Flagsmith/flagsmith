import logging
import sys

import requests

HEALTH_LIVENESS_URL = "http://localhost:8000/health/liveness"


logger = logging.getLogger(__name__)


def main() -> None:
    logger.warning(
        f"This healthcheck, invoked by {' '.join(sys.argv)}, is deprecated. "
        f"Use the `{HEALTH_LIVENESS_URL}` endpoint instead."
    )
    status_code = requests.get(HEALTH_LIVENESS_URL).status_code

    if status_code != 200:
        logger.error(f"Health check failed with status {status_code}")

    sys.exit(0 if 200 >= status_code < 300 else 1)


if __name__ == "__main__":
    main()
