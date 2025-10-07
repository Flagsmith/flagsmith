from typing import NotRequired, TypedDict


class BaseUserInfo(TypedDict):
    first_name: str
    last_name: str
    google_user_id: NotRequired[str]
    github_user_id: NotRequired[str]
    alternative_email_addresses: NotRequired[list[str]]


class UserInfo(BaseUserInfo):
    email: str
