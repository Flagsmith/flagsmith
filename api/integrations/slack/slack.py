from dataclasses import dataclass, field
from typing import List

from django.conf import settings
from slack_sdk import WebClient  # type: ignore[attr-defined]
from slack_sdk.errors import SlackApiError
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler

from audit.models import AuditLog
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
    def __init__(self, api_token: str = None, channel_id: str = None):  # type: ignore[assignment]
        self.api_token = api_token
        self.channel_id = channel_id

    def get_bot_token(self, code: str, redirect_uri: str) -> str:
        oauth_response = self._client.oauth_v2_access(
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            code=code,
            redirect_uri=redirect_uri,
        )
        return oauth_response.get("access_token")  # type: ignore[no-untyped-call,no-any-return]

    def join_channel(self):  # type: ignore[no-untyped-def]
        try:
            self._client.conversations_join(channel=self.channel_id)
        except SlackApiError as e:
            raise SlackChannelJoinError(e.response.get("error")) from e

    def get_channels_data(self, **kwargs) -> ChannelsDataResponse:  # type: ignore[no-untyped-def]
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
    def generate_event_data(audit_log_record: AuditLog) -> dict:  # type: ignore[type-arg]
        log = audit_log_record.log
        environment_name = audit_log_record.environment_name
        email = audit_log_record.author_identifier

        return {
            "blocks": [
                {"type": "section", "text": {"type": "plain_text", "text": log}},
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Environment:*\n{environment_name}",
                        },
                        {"type": "mrkdwn", "text": f"*User:*\n{email}"},
                    ],
                },
            ]
        }

    def _track_event(self, event: dict) -> None:  # type: ignore[type-arg]
        self._client.chat_postMessage(channel=self.channel_id, blocks=event["blocks"])
