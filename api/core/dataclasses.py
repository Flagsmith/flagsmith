from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.request import Request

    from api_keys.models import MasterAPIKey
    from users.models import FFAdminUser


@dataclass
class AuthorData:
    user: "FFAdminUser | None" = None
    api_key: "MasterAPIKey | None" = None

    def __post_init__(self) -> None:
        if self.user and self.api_key:
            raise ValueError("Author must be either a user or a MasterAPIKey")

    @classmethod
    def from_request(cls, request: "Request") -> "AuthorData":
        from users.models import FFAdminUser

        if type(request.user) is FFAdminUser:
            return cls(user=request.user)
        elif hasattr(request.user, "key"):
            return cls(api_key=request.user.key)
        else:
            raise ValueError("Request user must be FFAdminUser or have an API key")
