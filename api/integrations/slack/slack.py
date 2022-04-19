from dataclasses import dataclass, field
from typing import List

from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

from .exceptions import SlackChannelJoinError


@dataclass
class SlackChannel:
    channel_name: str
    channel_id: str


@dataclass
class ChannelsDataResponse:
    cursor: str
    channels: List[SlackChannel] = field(default_factory=list)


class SlackWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, api_token: str = None, channel_id: str = None):
        self.api_token = api_token
        self.channel_id = channel_id

    def get_bot_token(self, code: str, redirect_uri: str) -> str:
        oauth_response = self._client.oauth_v2_access(
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            code=code,
            redirect_uri=redirect_uri,
        )
        return oauth_response.get("access_token")

    def join_channel(self):
        try:
            self._client.conversations_join(channel=self.channel_id)
        except SlackApiError as e:
            raise SlackChannelJoinError(e.response.get("error")) from e

    def get_channels_data(self, **kwargs) -> ChannelsDataResponse:
        """
        Returns non archived public channels.
        """

        response = self._client.conversations_list(exclude_archived=True, **kwargs)
        channels = response["channels"]
        channels = [
            SlackChannel(channel["name"], channel["id"]) for channel in channels
        ]
        cursor = response["response_metadata"]["next_cursor"]
        return ChannelsDataResponse(channels=channels, cursor=cursor)

    @property
    def _client(self) -> WebClient:
        client = WebClient(token=self.api_token)
        client.retry_handlers.append(RateLimitErrorRetryHandler(max_retry_count=3))
        return client

    @staticmethod
    def generate_event_data(log: str, email: str, environment_name: str) -> dict:
        return {
            "text": f"{log} by user {email}",
            "title": "Flagsmith Feature Flag Event",
            "tags": [f"env:{environment_name}"],
        }

    def _track_event(self, event: dict) -> None:
        self._client.chat_postMessage(channel=self.channel_id, text=event["text"])
