import logging

import requests
from django.conf import settings
from requests import RequestException

from custom_auth.oauth.exceptions import GithubError
from custom_auth.oauth.helpers.github_helpers import (
    convert_response_data_to_dictionary,
    get_first_and_last_name,
)

GITHUB_API_URL = "https://api.github.com"
GITHUB_OAUTH_URL = "https://github.com/login/oauth"

NON_200_ERROR_MESSAGE = "Github returned {} status code when getting an access token."

logger = logging.getLogger(__name__)


class GithubUser:
    def __init__(self, code: str, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or settings.GITHUB_CLIENT_ID
        self.client_secret = client_secret or settings.GITHUB_CLIENT_SECRET

        self.access_token = self._get_access_token(code)
        self.headers = {"Authorization": f"token {self.access_token}"}

    def _get_access_token(self, code) -> str:
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(f"{GITHUB_OAUTH_URL}/access_token", data=data)

        if response.status_code != 200:
            raise GithubError(NON_200_ERROR_MESSAGE.format(response.status_code))

        response_json = convert_response_data_to_dictionary(response.text)
        if "error" in response_json:
            error_message = response_json["error_description"].replace("+", " ")
            raise GithubError(error_message)

        return response_json["access_token"]

    def get_user_info(self) -> dict:
        # TODO: use threads?
        try:
            return {**self._get_user_name_and_id(), "email": self._get_primary_email()}
        except RequestException:
            raise GithubError("Failed to communicate with the Github API.")

    def _get_user_name_and_id(self):
        user_response = requests.get(f"{GITHUB_API_URL}/user", headers=self.headers)
        user_response_json = user_response.json()
        full_name = user_response_json.get("name")
        first_name, last_name = (
            get_first_and_last_name(full_name) if full_name else ["", ""]
        )
        return {
            "first_name": first_name,
            "last_name": last_name,
            "github_user_id": user_response_json.get("id"),
        }

    def _get_primary_email(self):
        emails_response = requests.get(
            f"{GITHUB_API_URL}/user/emails", headers=self.headers
        )

        # response from github should be a list of dictionaries, this will find the first entry that is both verified
        # and marked as primary (there should only be one).
        primary_email_data = next(
            filter(
                lambda email_data: email_data["primary"] and email_data["verified"],
                emails_response.json(),
            ),
            None,
        )

        if not primary_email_data:
            raise GithubError(
                "User does not have a verified email address with Github."
            )

        return primary_email_data["email"]
