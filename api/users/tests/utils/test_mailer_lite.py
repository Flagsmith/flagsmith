import json

import pytest

from organisations.models import Organisation, Subscription
from users.models import FFAdminUser
from users.utils.mailer_lite import (
    BatchSubscribe,
    MailerLite,
    _get_request_body_from_user,
)


@pytest.mark.django_db
def test_mailer_lite_subscribe_calls_post_with_correct_arguments(mocker, settings):
    # Given
    mock_session = mocker.MagicMock()

    base_url = "http//localhost/mailer/test/"
    settings.MAILERLITE_BASE_URL = base_url
    resource = "/test"
    user = FFAdminUser.objects.create(
        email="test_user",
        first_name="test",
        last_name="test",
        marketing_consent_given=True,
    )
    mailer_lite = MailerLite(session=mock_session)

    mocker.patch("users.utils.mailer_lite.MailerLite.resource", resource)
    mocked_headers = mocker.patch(
        "users.utils.mailer_lite.MailerLiteBaseClient.request_headers",
    )
    # When
    mailer_lite._subscribe(user)
    # Then
    mock_session.post.assert_called_with(
        base_url + resource,
        data=json.dumps(
            {"email": user.email, "name": "test test", "fields": {"is_paid": False}}
        ),
        headers=mocked_headers,
    )


@pytest.mark.django_db
def test_batch_subscribe__subscribe_calls_batch_send_correct_number_of_times(mocker):
    # Given
    user1 = FFAdminUser.objects.create(
        email="test_user1", first_name="test", last_name="test"
    )
    user2 = FFAdminUser.objects.create(
        email="test_user2", first_name="test", last_name="test"
    )
    user3 = FFAdminUser.objects.create(
        email="test_user3", first_name="test", last_name="test"
    )

    users = [user1, user2, user3]

    mock_session = mocker.MagicMock()

    # When
    with BatchSubscribe(batch_size=2, session=mock_session) as batch:
        for user in users:
            batch.subscribe(user)

    # Then
    # assert that batch_send is called (using requests made) twice, first time for
    # hitting the maximum limit and second time
    # for exiting the context manager
    assert mock_session.post.call_count == 2


@pytest.mark.django_db
def test_batch_subscribe__subscribe_populates_batch_correctly(mocker):
    # Given
    user1 = FFAdminUser.objects.create(
        email="test_user1", first_name="test", last_name="test"
    )
    user2 = FFAdminUser.objects.create(
        email="test_user2", first_name="test", last_name="test"
    )
    users = [user1, user2]
    # When
    with BatchSubscribe() as batch:
        for user in users:
            batch.subscribe(user)
        # Then
        len(batch._batch) == len(users)
        assert batch._batch[0]["body"]["email"] == users[0].email
        assert batch._batch[1]["body"]["email"] == users[1].email


@pytest.mark.django_db
def test_get_request_body_from_user_with_paid_organisations(mocker):
    # Given
    user = FFAdminUser.objects.create(
        email="test_user1", first_name="test", last_name="test"
    )

    organisation = Organisation.objects.create(name="Test org")
    Subscription.objects.create(organisation=organisation)
    user.add_organisation(organisation)

    # When
    data = _get_request_body_from_user(user)

    # Then
    assert data == {
        "email": user.email,
        "name": "test test",
        "fields": {"is_paid": True},
    }


def test_batch_subscribe_batch_send_makes_correct_post_request(mocker, settings):

    # Given
    mock_session = mocker.MagicMock()
    mocked_headers = mocker.patch(
        "users.utils.mailer_lite.MailerLiteBaseClient.request_headers",
    )

    base_url = "http//localhost/mailer/test/"
    settings.MAILERLITE_BASE_URL = base_url
    resource = "batch"

    batch = BatchSubscribe(session=mock_session)
    test_batch_data = [1, 2, 3]

    mocker.patch.object(batch, "_batch", test_batch_data.copy())

    # When
    batch.batch_send()
    # Then
    mock_session.post.assert_called_with(
        base_url + resource,
        data=json.dumps({"requests": test_batch_data}),
        headers=mocked_headers,
    )
    assert batch._batch == []
