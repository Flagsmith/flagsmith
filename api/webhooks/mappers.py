import typing
from datetime import datetime

from webhooks.constants import WEBHOOK_DATETIME_FORMAT

if typing.TYPE_CHECKING:
    from api_keys.models import MasterAPIKey
    from users.models import FFAdminUser


def datetime_to_webhook_timestamp(dt: datetime) -> str:
    return dt.strftime(WEBHOOK_DATETIME_FORMAT)


def user_or_key_to_changed_by(
    user: "FFAdminUser | None" = None,
    api_key: "MasterAPIKey | None" = None,
) -> str:
    if user:
        return user.email
    if api_key:
        return api_key.name
    return ""
