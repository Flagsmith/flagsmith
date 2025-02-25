import sys

import requests


def main() -> None:
    url = "http://localhost:8000/health/liveness"
    status = requests.get(url).status_code

    sys.exit(0 if 200 >= status < 300 else 1)


if __name__ == "__main__":
    main()
