import pytest


@pytest.fixture
def mocked_slack_internal_client(mocker):
    mocked_client = mocker.MagicMock()

    mocker.patch(
        "integrations.slack.slack.SlackWrapper._client",
        new_callable=mocker.PropertyMock,
        return_value=mocked_client,
    )
    return mocked_client
