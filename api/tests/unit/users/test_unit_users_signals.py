import pytest

from users.models import FFAdminUser
from users.signals import create_pipedrive_lead_signal, warn_insecure


@pytest.mark.django_db
def test_warn_insecure_emits_a_warning_when_no_user_exists(recwarn, django_user_model):
    # When
    warn_insecure(django_user_model)

    # Then
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert issubclass(w.category, RuntimeWarning)


@pytest.mark.django_db
def test_warn_insecure_emits_no_warning_when_user_exists(
    admin_user, recwarn, django_user_model
):
    # When
    warn_insecure(django_user_model)

    # Then
    assert len(recwarn) == 0


def test_create_pipedrive_lead_signal_calls_task_if_user_created(
    mocker, settings, django_user_model
):
    # Given
    mocked_create_pipedrive_lead = mocker.patch("users.signals.create_pipedrive_lead")
    settings.ENABLE_PIPEDRIVE_LEAD_TRACKING = True

    # When
    user = django_user_model.objects.create(email="test@example.com")

    # Then
    mocked_create_pipedrive_lead.delay.assert_called_once_with(args=(user.id,))


def test_create_pipedrive_lead_signal_does_not_call_task_if_user_not_created(
    mocker, settings
):
    # Given
    mocked_create_pipedrive_lead = mocker.patch("users.signals.create_pipedrive_lead")
    user = mocker.MagicMock()

    settings.PIPEDRIVE_API_TOKEN = "some-token"

    # When
    create_pipedrive_lead_signal(FFAdminUser, instance=user, created=False)

    # Then
    mocked_create_pipedrive_lead.delay.assert_not_called()


def test_create_pipedrive_lead_signal_does_not_call_task_if_pipedrive_not_configured(
    mocker, settings
):
    # Given
    mocked_create_pipedrive_lead = mocker.patch("users.signals.create_pipedrive_lead")
    user = mocker.MagicMock()

    settings.PIPEDRIVE_API_TOKEN = None

    # When
    create_pipedrive_lead_signal(FFAdminUser, instance=user, created=False)

    # Then
    mocked_create_pipedrive_lead.delay.assert_not_called()
