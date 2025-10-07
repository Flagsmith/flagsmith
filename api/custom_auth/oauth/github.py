import logging
from typing import TypedDict

import requests
from django.conf import settings
from requests import RequestException

from custom_auth.oauth.exceptions import GithubError
from custom_auth.oauth.helpers.github_helpers import (
    convert_response_data_to_dictionary,
    get_first_and_last_name,
)
from custom_auth.oauth.types import BaseUserInfo, UserInfo

GITHUB_API_URL = "https://api.github.com"
GITHUB_OAUTH_URL = "https://github.com/login/oauth"

NON_200_ERROR_MESSAGE = "Github returned {} status code when getting an access token."

logger = logging.getLogger(__name__)


class GithubEmail(TypedDict):
    email: str
    primary: bool
    verified: bool


class GithubUser:
    def __init__(self, code: str, client_id: str = None, client_secret: str = None):  # type: ignore[assignment]
        self.client_id = client_id or settings.GITHUB_CLIENT_ID
        self.client_secret = client_secret or settings.GITHUB_CLIENT_SECRET

        self.access_token = self._get_access_token(code)
        self.headers = {"Authorization": f"token {self.access_token}"}

    def _get_access_token(self, code) -> str:  # type: ignore[no-untyped-def]
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

        return response_json["access_token"]  # type: ignore[no-any-return]

    def get_user_info(self) -> UserInfo:
        # TODO: use threads?
        try:
            base_user_info = self._get_user_name_and_id()
            emails = self._get_user_emails()

            primary_email = None
            alternative_email_addresses = []

            for email in emails:
                if not email["verified"]:
                    continue

                if email["primary"]:
                    primary_email = email["email"]
                else:
                    alternative_email_addresses.append(email["email"])

            if not primary_email:
                raise GithubError(
                    "User does not have a verified email address with Github."
                )

            return {
                "first_name": base_user_info["first_name"],
                "last_name": base_user_info["last_name"],
                "github_user_id": base_user_info["github_user_id"],
                "email": primary_email,
                "alternative_email_addresses": alternative_email_addresses,
            }

        except RequestException:
            raise GithubError("Failed to communicate with the Github API.")

    def _get_user_name_and_id(self) -> BaseUserInfo:
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

    def _get_user_emails(self) -> list[GithubEmail]:
        emails_response = requests.get(
            f"{GITHUB_API_URL}/user/emails", headers=self.headers
        )
        emails = []
        for email in emails_response.json():
            emails.append(
                GithubEmail(
                    email=email["email"],
                    primary=email["primary"],
                    verified=email["verified"],
                )
            )
        return emails
