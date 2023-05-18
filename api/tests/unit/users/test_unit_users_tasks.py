from django.core import mail

from users.tasks import (
    create_pipedrive_lead,
    send_email_changed_notification_email,
)


def test_create_pipedrive_lead(mocker, admin_user):
    # Given
    mock_lead_tracker = mocker.MagicMock()
    mocker.patch("users.tasks.PipedriveLeadTracker", return_value=mock_lead_tracker)

    # When
    create_pipedrive_lead(admin_user.id)

    # Then
    mock_lead_tracker.create_lead.assert_called_once_with(admin_user)


def test_send_email_changed_notification():
    # When
    send_email_changed_notification_email(
        first_name="first_name",
        from_email="fromtest@test.com",
        original_email="test2@test.com",
    )

    # Then
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Your Flagsmith email address has been changed"
    assert mail.outbox[0].from_email == "fromtest@test.com"
    assert mail.outbox[0].recipients() == ["test2@test.com"]
