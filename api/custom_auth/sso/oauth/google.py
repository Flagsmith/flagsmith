import requests
from requests import RequestException
from rest_framework import status

from custom_auth.sso.oauth.exceptions import GoogleError

USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&"
NON_200_ERROR_MESSAGE = "Google returned {} status code when getting an access token."


def get_user_info(access_token):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(USER_INFO_URL, headers=headers)

        if response.status_code != status.HTTP_200_OK:
            raise GoogleError(NON_200_ERROR_MESSAGE.format(response.status_code))

        response_json = response.json()
        return {
            "email": response_json["email"],
            "first_name": response_json.get("given_name", ""),
            "last_name": response_json.get("family_name", ""),
            "google_user_id": response_json["id"],
        }
    except RequestException:
        raise GoogleError("Failed to communicate with the Google API.")
