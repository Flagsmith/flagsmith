import pytest
import requests
import responses
from pytest_mock import MockerFixture
from pytest_structlog import StructuredLogCapture

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook
from integrations.gitlab.services.webhooks import (
    deregister_webhook_for_path,
    ensure_webhook_registered,
)
from integrations.gitlab.tasks import register_gitlab_webhook


@pytest.mark.django_db
@responses.activate
def test_ensure_webhook_registered__gitlab_http_error__logs_and_raises(
    gitlab_config: GitLabConfiguration,
    log: StructuredLogCapture,
    mocker: MockerFixture,
) -> None:
    # Given — GitLab rejects the hook creation.
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/hooks",
        status=500,
    )

    # When / Then
    with pytest.raises(requests.RequestException):
        ensure_webhook_registered(gitlab_config, "testorg/testrepo")

    assert log.events == [
        {
            "level": "error",
            "event": "webhook.registration_failed",
            "organisation__id": gitlab_config.project.organisation_id,
            "project__id": gitlab_config.project_id,
            "gitlab__project__path": "testorg/testrepo",
            "exc_info": mocker.ANY,
        },
    ]
    assert not GitLabWebhook.objects.exists()


@pytest.mark.django_db
def test_deregister_webhook_for_path__no_matching_webhook__noop(
    gitlab_config: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given / When — no webhook row exists for this (config, path) pair.
    deregister_webhook_for_path(gitlab_config, "never/registered")

    # Then — nothing logged, nothing raised.
    assert log.events == []


@pytest.mark.django_db
def test_register_gitlab_webhook_task__config_missing__noop(
    log: StructuredLogCapture,
) -> None:
    # Given / When — a stale task fires after the config was hard-deleted.
    register_gitlab_webhook(config_id=999_999, project_path="testorg/testrepo")

    # Then — no webhook created, no log.
    assert not GitLabWebhook.objects.exists()
    assert log.events == []


@pytest.mark.django_db
def test_deregister_gitlab_webhook_hook__unparseable_url__noop(
    gitlab_config: GitLabConfiguration,
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given — a GitLab-typed link whose URL doesn't match the issue/MR shape.
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/not-a-resource",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )

    # When
    resource.delete()

    # Then — no deregistration attempted.
    assert log.events == []


@pytest.mark.django_db
def test_deregister_gitlab_webhook_hook__no_config__noop(
    feature: Feature,
    log: StructuredLogCapture,
) -> None:
    # Given — a GitLab-typed link exists but the config was removed.
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        feature=feature,
    )

    # When
    resource.delete()

    # Then — no deregistration attempted.
    assert log.events == []
