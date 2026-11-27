import json

import pytest
import responses
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.signals import send_audit_log_event_to_discord
from environments.models import Environment
from integrations.discord.discord import EMBED_TITLE_LIMIT, DiscordWrapper
from integrations.discord.models import DiscordConfiguration
from projects.models import Project

WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc-DEF_1"


def test_discord_wrapper__generate_event_data__embed_with_project_environment_and_author(
    project: Project,
    environment: Environment,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        environment=environment,
        log="Flag state updated for feature: dark_mode",
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
    )

    # When
    event = DiscordWrapper.generate_event_data(audit_log_record)

    # Then
    embed = event["embeds"][0]
    assert embed["title"] == "Flag state updated for feature: dark_mode"
    assert f"**Project:** {project.name}" in embed["description"]
    assert f"**Environment:** {environment.name}" in embed["description"]
    assert "**By:** " in embed["description"]
    assert embed["timestamp"] == audit_log_record.created_date.isoformat()
    assert event["allowed_mentions"] == {"parse": []}


def test_discord_wrapper__generate_event_data_long_log__title_clipped(
    project: Project,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        log="x" * 400,
        related_object_type=RelatedObjectType.FEATURE.name,
    )

    # When
    event = DiscordWrapper.generate_event_data(audit_log_record)

    # Then
    title = event["embeds"][0]["title"]
    assert len(title) == EMBED_TITLE_LIMIT
    assert title.endswith("…")
    assert "**Environment:**" not in event["embeds"][0]["description"]


@responses.activate()
def test_discord_wrapper__track_event__posts_json_to_webhook() -> None:
    # Given
    wrapper = DiscordWrapper(webhook_url=WEBHOOK_URL)
    event = {"embeds": [{"title": "hello"}]}
    responses.add(url=WEBHOOK_URL, method="POST", status=204)

    # When
    wrapper._track_event(event)

    # Then
    assert len(responses.calls) == 1
    assert json.loads(responses.calls[0].request.body) == event  # type: ignore[union-attr]


@responses.activate()
def test_discord_wrapper__track_event_webhook_deleted__logs_failure(
    log: StructuredLogCapture,
) -> None:
    # Given
    wrapper = DiscordWrapper(webhook_url=WEBHOOK_URL)
    responses.add(url=WEBHOOK_URL, method="POST", status=404)

    # When
    wrapper._track_event({"embeds": []})

    # Then
    assert log.events == [
        {
            "level": "warning",
            "event": "webhook.failed",
            "response__status_code": 404,
        }
    ]


def test_send_audit_log_event_to_discord__project_config__calls_expected(
    mocker: MockerFixture,
    project: Project,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    wrapper_mock = mocker.patch("audit.signals.DiscordWrapper", autospec=True)
    DiscordConfiguration.objects.create(project=project, base_url=WEBHOOK_URL)
    project.refresh_from_db()

    # When
    send_audit_log_event_to_discord(AuditLog, audit_log_record)

    # Then
    wrapper_mock.assert_called_once_with(webhook_url=WEBHOOK_URL)
    instance = wrapper_mock.return_value
    instance.generate_event_data.assert_called_once_with(
        audit_log_record=audit_log_record
    )
    instance.track_event_async.assert_called_once_with(
        event=instance.generate_event_data.return_value
    )


def test_send_audit_log_event_to_discord__no_config__does_nothing(
    mocker: MockerFixture,
    project: Project,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    wrapper_mock = mocker.patch("audit.signals.DiscordWrapper", autospec=True)

    # When
    send_audit_log_event_to_discord(AuditLog, audit_log_record)

    # Then
    wrapper_mock.assert_not_called()


@pytest.mark.parametrize(
    "related_object_type",
    [RelatedObjectType.ENVIRONMENT, RelatedObjectType.CHANGE_REQUEST],
)
def test_send_audit_log_event_to_discord__unrelated_event__ignored(
    mocker: MockerFixture,
    project: Project,
    related_object_type: RelatedObjectType,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=related_object_type.name,
    )
    wrapper_mock = mocker.patch("audit.signals.DiscordWrapper", autospec=True)
    DiscordConfiguration.objects.create(project=project, base_url=WEBHOOK_URL)
    project.refresh_from_db()

    # When
    send_audit_log_event_to_discord(AuditLog, audit_log_record)

    # Then
    wrapper_mock.assert_not_called()
