from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application

from oauth2_metadata.tasks import (
    cleanup_stale_oauth2_applications,
    clear_expired_oauth2_tokens,
)


def test_clear_expired_oauth2_tokens__called__invokes_cleartokens_command(
    mocker: MagicMock,
) -> None:
    # Given
    mock_call_command = mocker.patch("oauth2_metadata.tasks.call_command")

    # When
    clear_expired_oauth2_tokens()

    # Then
    mock_call_command.assert_called_once_with("cleartokens")



@pytest.mark.django_db()
def test_cleanup_stale_oauth2_applications__stale_app__deletes_it(
    mocker: MagicMock,
) -> None:
    # Given - an app created 15 days ago with no tokens
    app = Application.objects.create(
        name="Stale App",
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )
    Application.objects.filter(pk=app.pk).update(
        created=timezone.now() - timedelta(days=15),
    )

    # When
    cleanup_stale_oauth2_applications()

    # Then
    assert not Application.objects.filter(pk=app.pk).exists()


@pytest.mark.django_db()
def test_cleanup_stale_oauth2_applications__app_with_token__keeps_it(
    admin_user: None,
    mocker: MagicMock,
) -> None:
    # Given - an old app that has an access token
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = User.objects.first()
    app = Application.objects.create(
        name="Active App",
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )
    Application.objects.filter(pk=app.pk).update(
        created=timezone.now() - timedelta(days=15),
    )
    AccessToken.objects.create(
        user=user,
        application=app,
        token="test-token",
        expires=timezone.now() + timedelta(hours=1),
    )

    # When
    cleanup_stale_oauth2_applications()

    # Then
    assert Application.objects.filter(pk=app.pk).exists()


@pytest.mark.django_db()
def test_cleanup_stale_oauth2_applications__recent_app__keeps_it(
    mocker: MagicMock,
) -> None:
    # Given - an app created 5 days ago with no tokens
    app = Application.objects.create(
        name="Recent App",
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris="https://example.com/callback",
    )
    Application.objects.filter(pk=app.pk).update(
        created=timezone.now() - timedelta(days=5),
    )

    # When
    cleanup_stale_oauth2_applications()

    # Then
    assert Application.objects.filter(pk=app.pk).exists()
