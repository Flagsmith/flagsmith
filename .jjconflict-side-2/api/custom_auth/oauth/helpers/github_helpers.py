import logging

from custom_auth.oauth.exceptions import GithubError

logger = logging.getLogger(__name__)


def convert_response_data_to_dictionary(text: str) -> dict:  # type: ignore[type-arg]
    try:
        response_data = {}
        for key, value in [param.split("=") for param in text.split("&")]:
            response_data[key] = value
        return response_data
    except ValueError:
        logger.warning("Malformed data received from Github (%s)" % text)
        raise GithubError("Malformed data received from Github")


def get_first_and_last_name(full_name: str) -> list:  # type: ignore[type-arg]
    if not full_name:
        return ["", ""]

    names = full_name.strip().split(" ")
    return names if len(names) == 2 else [full_name, ""]
