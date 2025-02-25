import logging
import sys

import requests


def main() -> None:
    logging.getLogger(__name__).warning(
        "`python scripts/healthcheck.py` is deprecated. "
        "Use the `health/liveness` endpoint instead."
    )
    url = "http://localhost:8000/health/liveness"
    status = requests.get(url).status_code

    sys.exit(0 if 200 >= status < 300 else 1)


if __name__ == "__main__":
    main()
