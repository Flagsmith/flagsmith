from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper


class SlackWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, api_token: str, channel_id: str):
        self.client = get_client(api_token)
        self.channel_id = channel_id

    def _track_event(self, event: dict) -> None:
        print(f"Sending event {event} to slack")
        self.client.chat_postMessage(channel=self.channel_id, text=event["text"])

    @staticmethod
    def generate_event_data(log: str, email: str, environment_name: str) -> dict:
        return {
            "text": f"{log} by user {email}",
            "title": "Flagsmith Feature Flag Event",
            "tags": [f"env:{environment_name}"],
        }


def get_bot_token(code: str, redirect_uri: str) -> str:
    client = WebClient()
    oauth_response = client.oauth_v2_access(
        client_id=settings.SLACK_CLIENT_ID,
        client_secret=settings.SLACK_CLIENT_SECRET,
        code=code,
        redirect_uri=redirect_uri,
    )
    return oauth_response.get("access_token")


def join_channel(api_token: str, channel: str) -> None:
    client = get_client(api_token)
    client.conversations_join(channel=channel)


def get_client(api_token: str = None) -> WebClient:
    client = WebClient(token=api_token)
    client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=3))
    return client


def get_channels_data(api_token: str) -> dict:
    """
    Returns a dictionary with channel_name and channel_id of non archived
    public channels.
    """

    client = get_client(api_token)
    response = client.conversations_list(exclude_archived=True)
    conversations = response["channels"]
    channel_data = [
        {"channel_name": channel["name"], "channel_id": channel["id"]}
        for channel in conversations
    ]
    return channel_data
