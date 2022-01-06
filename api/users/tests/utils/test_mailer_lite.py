import json

import pytest

from organisations.models import Organisation, Subscription
from users.models import FFAdminUser
from users.utils.mailer_lite import (
    BatchSubscribe,
    MailerLite,
    MailerLiteBaseClient,
    _get_request_body_from_user,
)


@pytest.mark.django_db
def test_mailer_lite_subscribe_calls_post_with_correct_arguments(mocker, settings):
    # Given
    mocked_requests = mocker.patch("users.utils.mailer_lite.requests")
    base_url = "http//localhost/mailer/test/"
    settings.MAILERLITE_BASE_URL = base_url
    resource = "subscribers"

    user = FFAdminUser.objects.create(
        email="test_user",
        first_name="test",
        last_name="test",
        marketing_consent_given=True,
    )
    mailer_lite = MailerLite()
    mocked_headers = mocker.patch(
        "users.utils.mailer_lite.MailerLiteBaseClient._request_headers",
        new_callable=mocker.PropertyMock,
    ).return_value
    # When
    mailer_lite._subscribe(user)
    # Then
    mocked_requests.post.assert_called_with(
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
    mocker.patch("users.utils.mailer_lite.MAX_BATCH_SIZE", 2)
    mocked_batch_send = mocker.patch(
        "users.utils.mailer_lite.BatchSubscribe.batch_send"
    )
    # When
    with BatchSubscribe() as batch:
        for user in users:
            batch.subscribe(user)
    # Then
    # assert that batch_send is call twice, first time for
    # hitting the maximum limit and second time
    # for exiting the context manager
    assert mocked_batch_send.call_count == 2


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


def test_batch_subscribe_batch_send_clears_internal_batch(mocker):
    # Given
    batch = BatchSubscribe()
    batch._batch = ["some_value"]
    mocker.patch("users.utils.mailer_lite.requests")

    # When
    batch.batch_send()

    # Then
    assert batch._batch == []


def test_batch_subscribe_batch_send_makes_correct_post_request(mocker, settings):

    # Given
    mocked_request = mocker.patch("users.utils.mailer_lite.requests")
    mocked_headers = mocker.patch(
        "users.utils.mailer_lite.MailerLiteBaseClient._request_headers",
        new_callable=mocker.PropertyMock,
    ).return_value

    base_url = "http//localhost/mailer/test/"
    settings.MAILERLITE_BASE_URL = base_url
    resource = "batch"

    batch = BatchSubscribe()
    test_batch_data = [1, 2, 3]

    mocker.patch.object(batch, "_batch", test_batch_data.copy())

    # When
    batch.batch_send()
    # Then
    mocked_request.post.assert_called_with(
        base_url + resource,
        data=json.dumps({"requests": test_batch_data}),
        headers=mocked_headers,
    )


def test_mailer_lite_base_client_request_headers(settings):
    # Given
    api_key = "test_key"
    settings.MAILERLITE_API_KEY = api_key
    # When
    headers = MailerLiteBaseClient()._request_headers
    assert headers == {
        "X-MailerLite-ApiKey": api_key,
        "Content-Type": "application/json",
    }
