from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rest_framework.request import Request

    from api_keys.models import MasterAPIKey
    from api_keys.user import APIKeyUser
    from users.models import FFAdminUser


@dataclass
class AuthorData:
    user: "FFAdminUser | None" = None
    api_key: "MasterAPIKey | None" = None

    @classmethod
    def from_request(cls, request: "Request") -> "AuthorData":
        from users.models import FFAdminUser

        if type(request.user) is FFAdminUser:
            return cls(user=request.user)
        elif hasattr(request.user, "key"):
            return cls(api_key=request.user.key)
        else:
            raise ValueError("Request user must be FFAdminUser or have an API key")

    @classmethod
    def from_user(cls, user: "FFAdminUser | APIKeyUser") -> "AuthorData":
        from users.models import FFAdminUser

        # `UserABC.__subclasshook__` matches any user against `APIKeyUser`.
        if isinstance(user, FFAdminUser):
            return cls(user=user)
        return cls(api_key=user.key)
