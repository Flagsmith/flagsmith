import json

import responses
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.signals import (
    call_webhooks,
    send_audit_log_event_to_dynatrace,
    send_audit_log_event_to_grafana,
)
from environments.models import Environment
from features.models import Feature
from features.versioning.models import EnvironmentFeatureVersion
from integrations.dynatrace.dynatrace import EVENTS_API_URI
from integrations.dynatrace.models import DynatraceConfiguration
from integrations.grafana.grafana import ROUTE_API_ANNOTATIONS
from integrations.grafana.models import (
    GrafanaOrganisationConfiguration,
    GrafanaProjectConfiguration,
)
from organisations.models import Organisation, OrganisationWebhook
from projects.models import Project
from projects.tags.models import Tag
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType


def test_call_webhooks_does_not_create_task_if_webhooks_disabled(
    organisation: Organisation,
    project: Project,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    audit_log = AuditLog(project=project)
    settings.DISABLE_WEBHOOKS = True

    mocked_call_organisation_webhooks = mocker.patch(
        "audit.signals.call_organisation_webhooks"
    )

    # When
    call_webhooks(sender=AuditLog, instance=audit_log)  # type: ignore[no-untyped-call]

    # Then
    mocked_call_organisation_webhooks.delay.assert_not_called()


def test_call_webhooks_does_not_create_task_if_organisation_has_no_webhooks(
    organisation: Organisation,
    project: Project,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    audit_log = AuditLog(project=project)
    settings.DISABLE_WEBHOOKS = False

    assert organisation.webhooks.count() == 0

    mocked_call_organisation_webhooks = mocker.patch(
        "audit.signals.call_organisation_webhooks"
    )

    # When
    call_webhooks(sender=AuditLog, instance=audit_log)  # type: ignore[no-untyped-call]

    # Then
    mocked_call_organisation_webhooks.delay.assert_not_called()


def test_call_webhooks_creates_task_if_organisation_has_webhooks(
    organisation: Organisation,
    project: Project,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    audit_log = AuditLog.objects.create(project=project)
    OrganisationWebhook.objects.create(
        organisation=organisation,
        name="Example webhook",
        url="http://example.com/webhook",
        enabled=True,
    )
    settings.DISABLE_WEBHOOKS = False

    mocked_call_organisation_webhooks = mocker.patch(
        "audit.signals.call_organisation_webhooks"
    )

    # When
    call_webhooks(sender=AuditLog, instance=audit_log)  # type: ignore[no-untyped-call]

    # Then
    mocked_call_organisation_webhooks.delay.assert_called_once()
    mock_call = mocked_call_organisation_webhooks.delay.call_args.kwargs
    assert mock_call["args"][0] == organisation.id
    assert mock_call["args"][1]["id"] == audit_log.id
    assert mock_call["args"][2] == WebhookEventType.AUDIT_LOG_CREATED.name


def test_send_audit_log_event_to_grafana__project_grafana_config__calls_expected(
    mocker: MockerFixture,
    project: Project,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    grafana_wrapper_mock = mocker.patch("audit.signals.GrafanaWrapper", autospec=True)
    grafana_wrapper_instance_mock = grafana_wrapper_mock.return_value

    grafana_config = GrafanaProjectConfiguration(base_url="test.com", api_key="test")
    project.grafana_config = grafana_config

    # When
    send_audit_log_event_to_grafana(AuditLog, audit_log_record)

    # Then
    grafana_wrapper_mock.assert_called_once_with(
        base_url=grafana_config.base_url,
        api_key=grafana_config.api_key,
    )
    grafana_wrapper_instance_mock.generate_event_data.assert_called_once_with(
        audit_log_record
    )
    grafana_wrapper_instance_mock.track_event_async.assert_called_once_with(
        event=grafana_wrapper_instance_mock.generate_event_data.return_value
    )


def test_send_audit_log_event_to_grafana__organisation_grafana_config__calls_expected(
    mocker: MockerFixture,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    grafana_wrapper_mock = mocker.patch("audit.signals.GrafanaWrapper", autospec=True)
    grafana_wrapper_instance_mock = grafana_wrapper_mock.return_value

    grafana_config = GrafanaOrganisationConfiguration(
        base_url="test.com", api_key="test"
    )
    organisation.grafana_config = grafana_config

    # When
    send_audit_log_event_to_grafana(AuditLog, audit_log_record)

    # Then
    grafana_wrapper_mock.assert_called_once_with(
        base_url=grafana_config.base_url,
        api_key=grafana_config.api_key,
    )
    grafana_wrapper_instance_mock.generate_event_data.assert_called_once_with(
        audit_log_record
    )
    grafana_wrapper_instance_mock.track_event_async.assert_called_once_with(
        event=grafana_wrapper_instance_mock.generate_event_data.return_value
    )


def test_send_audit_log_event_to_grafana__organisation_grafana_config__deleted__doesnt_call(
    mocker: MockerFixture,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    grafana_wrapper_mock = mocker.patch("audit.signals.GrafanaWrapper", autospec=True)

    grafana_config = GrafanaOrganisationConfiguration(
        base_url="test.com", api_key="test"
    )
    organisation.grafana_config = grafana_config
    grafana_config.delete()

    # When
    send_audit_log_event_to_grafana(AuditLog, audit_log_record)

    # Then
    grafana_wrapper_mock.assert_not_called()


@responses.activate
def test_send_environment_feature_version_audit_log_event_to_grafana(
    tagged_feature: Feature,
    tag_one: Tag,
    tag_two: Tag,
    environment_v2_versioning: Environment,
    project: Project,
    organisation: Organisation,
    admin_user: FFAdminUser,
) -> None:
    # Given
    _, audit_log_record = _create_and_publish_environment_feature_version(
        environment=environment_v2_versioning,
        feature=tagged_feature,
        user=admin_user,
    )

    base_url = "https://test.com"
    GrafanaOrganisationConfiguration.objects.create(
        base_url=base_url, api_key="test", organisation=organisation
    )

    responses.add(
        method=responses.POST,
        url=f"{base_url}{ROUTE_API_ANNOTATIONS}",
        status=200,
        json={
            "message": "Annotation added",
            "id": 1,
        },
    )

    # When
    send_audit_log_event_to_grafana(AuditLog, audit_log_record)

    # Then
    expected_time = int(audit_log_record.created_date.timestamp() * 1000)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.body == json.dumps(  # type: ignore[union-attr]
        {
            "tags": [
                "flagsmith",
                f"project:{project.name}",
                f"environment:{environment_v2_versioning.name}",
                f"by:{admin_user.email}",
                f"feature:{tagged_feature.name}",
                tag_one.label,
                tag_two.label,
            ],
            "text": audit_log_record.log,
            "time": expected_time,
            "timeEnd": expected_time,
        }
    )


def test_send_audit_log_event_to_dynatrace__environment_dynatrace_config__calls_expected(
    mocker: MockerFixture,
    environment: Environment,
) -> None:
    # Given
    audit_log_record = AuditLog.objects.create(
        environment=environment,
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    dynatrace_wrapper_mock = mocker.patch(
        "audit.signals.DynatraceWrapper", autospec=True
    )
    dynatrace_wrapper_instance_mock = dynatrace_wrapper_mock.return_value

    dynatrace_config = DynatraceConfiguration.objects.create(
        base_url="http://test.com", api_key="api_123", environment=environment
    )

    # When
    send_audit_log_event_to_dynatrace(AuditLog, audit_log_record)

    # Then
    dynatrace_wrapper_mock.assert_called_once_with(
        base_url=dynatrace_config.base_url,
        api_key=dynatrace_config.api_key,
        entity_selector=dynatrace_config.entity_selector,
    )
    dynatrace_wrapper_instance_mock.generate_event_data.assert_called_once_with(
        audit_log_record
    )
    dynatrace_wrapper_instance_mock.track_event_async.assert_called_once_with(
        event=dynatrace_wrapper_instance_mock.generate_event_data.return_value
    )


@responses.activate
def test_send_environment_feature_version_audit_log_event_to_dynatrace(
    feature: Feature,
    environment_v2_versioning: Environment,
    project: Project,
    organisation: Organisation,
    admin_user: FFAdminUser,
) -> None:
    # Given
    _, audit_log_record = _create_and_publish_environment_feature_version(
        environment=environment_v2_versioning, feature=feature, user=admin_user
    )

    base_url = "https://dynatrace.test.com"
    api_key = "api_123"
    DynatraceConfiguration.objects.create(
        base_url=base_url, api_key=api_key, environment=environment_v2_versioning
    )

    responses.add(
        method=responses.POST,
        url=f"{base_url}{EVENTS_API_URI}?api-token={api_key}",
        status=201,
        json={
            "reportCount": 1,
            "eventIngestResults": [{"correlationId": "foobar123456", "status": "OK"}],
        },
    )

    # When
    send_audit_log_event_to_dynatrace(AuditLog, audit_log_record)

    # Then
    assert len(responses.calls) == 1
    assert json.loads(responses.calls[0].request.body) == {  # type: ignore[union-attr]
        "title": "Flagsmith flag change.",
        "eventType": "CUSTOM_DEPLOYMENT",
        "properties": {
            "event": f"{audit_log_record.log} by user {admin_user.email}",
            "environment": environment_v2_versioning.name,
            "dt.event.deployment.name": f"Flagsmith Deployment - Flag Changed: {feature.name}",
        },
        "entitySelector": "",
    }


def _create_and_publish_environment_feature_version(
    environment: Environment,
    feature: Feature,
    user: FFAdminUser,
) -> (EnvironmentFeatureVersion, AuditLog):  # type: ignore[syntax]
    version = EnvironmentFeatureVersion(
        environment=environment,
        feature=feature,
    )
    version.publish(user)

    audit_log_record = (
        AuditLog.objects.filter(
            related_object_uuid=version.uuid,
            related_object_type=RelatedObjectType.EF_VERSION.name,
        )
        .order_by("-created_date")
        .first()
    )
    return version, audit_log_record
