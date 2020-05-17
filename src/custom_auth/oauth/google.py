import requests

USER_INFO_URL = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json&"


def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(USER_INFO_URL, headers=headers)
    response_json = response.json()
    return {
        "email": response_json["email"],
        "first_name": response_json.get("given_name", ""),
        "last_name": response_json.get("family_name", ""),
        "google_user_id": response_json["id"]
    }
