from django.core import mail

from users.tasks import (
    send_email_changed_notification_email,
)


def test_send_email_changed_notification():  # type: ignore[no-untyped-def]
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
