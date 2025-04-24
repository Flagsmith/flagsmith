import logging
import sys

from common.core.main import main

if __name__ == "__main__":
    logging.getLogger(__name__).warning(
        f"This healthcheck, invoked by `{' '.join(sys.argv)}``, is deprecated. "
        "Please use one of the `flagsmith healthcheck` commands instead."
    )
    main(["flagsmith", "healthcheck", "http"])
