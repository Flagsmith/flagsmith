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

    @classmethod
    def from_request(cls, request: "Request") -> "AuthorData":
        return cls.from_user(request.user)

    @classmethod
    def from_user(cls, user: object) -> "AuthorData":
        from users.models import FFAdminUser

        if type(user) is FFAdminUser:
            return cls(user=user)
        elif hasattr(user, "key"):
            return cls(api_key=user.key)
        else:
            raise ValueError("User must be FFAdminUser or have an API key")
