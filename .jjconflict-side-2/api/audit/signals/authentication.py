from typing import Any

from axes.signals import user_locked_out  # type: ignore[import-untyped]
from django.conf import settings
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.http import HttpRequest
from oauth2_provider.models import AccessToken, Application
from oauth2_provider.signals import app_authorized

from audit.constants import (
    SSO_PROVIDER_NAMES,
    USER_2FA_DISABLED_MESSAGE,
    USER_2FA_ENABLED_MESSAGE,
    USER_LOCKED_OUT_MESSAGE,
    USER_LOGGED_IN_TO_OAUTH_APPLICATION_MESSAGE,
    USER_LOGGED_IN_WITH_2FA_MESSAGE,
    USER_LOGGED_IN_WITH_SSO_MESSAGE,
    USER_LOGGED_IN_WITHOUT_2FA_MESSAGE,
    USER_LOGGED_OUT_MESSAGE,
    USER_LOGGED_OUT_OF_OAUTH_APPLICATION_MESSAGE,
    USER_LOGIN_2FA_CODE_REJECTED_MESSAGE,
    USER_LOGIN_PASSWORD_REJECTED_MESSAGE,
    USER_LOGIN_REQUIRES_2FA_MESSAGE,
    USER_LOGIN_WHILE_LOCKED_OUT_MESSAGE,
    USER_PASSWORD_CHANGED_MESSAGE,
)
from audit.models import AuditLog
from audit.types import AxesLoginRequest
from custom_auth.signals import (
    user_2fa_disabled,
    user_2fa_enabled,
    user_login_2fa_code_rejected,
    user_login_2fa_code_verified,
    user_login_password_rejected,
    user_login_password_verified,
    user_login_sso_completed,
    user_password_changed,
)
from oauth2_metadata.signals import oauth_session_revoked
from users.auth_type import AuthType
from users.models import FFAdminUser


def _create_user_audit_logs(user: FFAdminUser, log: str) -> None:
    # We don't bulk_create because we need the post_save signal triggered
    for organisation in user.organisations.all():
        AuditLog.objects.create(organisation=organisation, author=user, log=log)


@receiver(user_login_password_verified)
def create_user_login_password_verified_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    is_2fa_required: bool,
    **kwargs: Any,
) -> None:
    message = (
        USER_LOGIN_REQUIRES_2FA_MESSAGE
        if is_2fa_required
        else USER_LOGGED_IN_WITHOUT_2FA_MESSAGE
    )
    _create_user_audit_logs(user, message % user.email)


@receiver(user_login_password_rejected)
def create_user_login_password_rejected_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(user, USER_LOGIN_PASSWORD_REJECTED_MESSAGE % user.email)


@receiver(user_login_2fa_code_verified)
def create_user_login_2fa_code_verified_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(user, USER_LOGGED_IN_WITH_2FA_MESSAGE % user.email)


@receiver(user_login_2fa_code_rejected)
def create_user_login_2fa_code_rejected_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(user, USER_LOGIN_2FA_CODE_REJECTED_MESSAGE % user.email)


@receiver(user_locked_out)
def create_user_locked_out_audit_logs(
    sender: str,
    request: AxesLoginRequest,
    username: str,
    **kwargs: Any,
) -> None:
    try:
        user = FFAdminUser.objects.get_by_natural_key(username)
    except FFAdminUser.DoesNotExist:
        return
    message = (
        USER_LOGIN_WHILE_LOCKED_OUT_MESSAGE
        if request.axes_failures_since_start > settings.AXES_FAILURE_LIMIT
        else USER_LOCKED_OUT_MESSAGE
    )
    _create_user_audit_logs(user, message % user.email)


@receiver(user_login_sso_completed)
def create_user_login_sso_completed_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    auth_type: AuthType,
    **kwargs: Any,
) -> None:
    provider_name = SSO_PROVIDER_NAMES[auth_type]
    _create_user_audit_logs(
        user, USER_LOGGED_IN_WITH_SSO_MESSAGE % (user.email, provider_name)
    )


@receiver(app_authorized)
def create_user_oauth_login_audit_logs(
    sender: object,
    request: HttpRequest,
    token: AccessToken,
    **kwargs: Any,
) -> None:
    if request.POST.get("grant_type") != "authorization_code":
        return  # pragma: no cover
    user: FFAdminUser = token.user
    _create_user_audit_logs(
        user,
        USER_LOGGED_IN_TO_OAUTH_APPLICATION_MESSAGE
        % (user.email, token.application.name),
    )


@receiver(oauth_session_revoked)
def create_user_oauth_logout_audit_logs(
    sender: object,
    user: FFAdminUser,
    application: Application,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(
        user,
        USER_LOGGED_OUT_OF_OAUTH_APPLICATION_MESSAGE % (user.email, application.name),
    )


@receiver(user_2fa_enabled)
def create_user_2fa_enabled_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(user, USER_2FA_ENABLED_MESSAGE % user.email)


@receiver(user_2fa_disabled)
def create_user_2fa_disabled_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(user, USER_2FA_DISABLED_MESSAGE % user.email)


@receiver(user_logged_out)
def create_user_logged_out_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser | None,
    **kwargs: Any,
) -> None:
    if user is None:
        return
    _create_user_audit_logs(user, USER_LOGGED_OUT_MESSAGE % user.email)


@receiver(user_password_changed)
def create_user_password_changed_audit_logs(
    sender: type[FFAdminUser],
    user: FFAdminUser,
    **kwargs: Any,
) -> None:
    _create_user_audit_logs(user, USER_PASSWORD_CHANGED_MESSAGE % user.email)
