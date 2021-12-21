from users.utils.mailer_lite import MailerLite


def test_mailer_lite_initialized_correctly(settings):
    # Given
    base_url = "http//localhost/mailer/test/"
    settings.MAILERLITE_API_KEY = "test_key"
    settings.MAILERLITE_BASE_URL = base_url

    # When
    mailer_lite = MailerLite()

    # Then
    assert mailer_lite.url == base_url + "subscribers"
    assert mailer_lite.headers == {"X-MailerLite-ApiKey": settings.MAILERLITE_API_KEY}


def test_mailer_lite_subscribe_calls_post_with_correct_arguments(mocker):
    # Given
    mocked_requests = mocker.patch("users.utils.mailer_lite.requests")

    mailer_lite = MailerLite()
    mocked_url = mocker.patch.object(mailer_lite, "url")
    mocked_headers = mocker.patch.object(mailer_lite, "headers")
    data = {"key": "value"}
    # When
    mailer_lite.subscribe(data)

    # Then
    mocked_requests.post.assert_called_with(
        mocked_url, data=data, headers=mocked_headers
    )
