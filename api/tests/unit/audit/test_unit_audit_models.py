import json

import pytest
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.serializers import AuditLogListSerializer
from integrations.datadog.models import DataDogConfiguration
from organisations.models import Organisation, OrganisationWebhook
from projects.models import Project
from webhooks.webhooks import WebhookEventType


def test_audit_log_save__organisation_webhook_exists__calls_organisation_webhooks(
    project: Project, mocker: MockerFixture, organisation: Organisation
) -> None:
    # Given
    mock_call_webhooks = mocker.patch("audit.signals.call_organisation_webhooks")

    audit_log = AuditLog(project=project, log="Some audit log")

    OrganisationWebhook.objects.create(
        organisation=organisation,
        url="http://example.com/webhook",
        enabled=True,
        name="example webhook",
    )

    # When
    audit_log.save()

    # Then
    mock_call_webhooks.delay.assert_called_once_with(
        args=(
            project.organisation.id,
            AuditLogListSerializer(instance=audit_log).data,
            WebhookEventType.AUDIT_LOG_CREATED.value,
        )
    )


def test_audit_log_save__datadog_not_configured__does_not_call_track_event(  # type: ignore[no-untyped-def]
    project, mocker
):
    # Given
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )
    audit_log = AuditLog(project=project, log="Some audit log")

    # When
    audit_log.save()

    # Then
    datadog_mock.track_event_async.assert_not_called()


def test_audit_log_save__datadog_configured_with_wrong_type__does_not_call_track_event(
    mocker, project
):  # type: ignore[no-untyped-def]  # noqa: E501
    # Given
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )

    DataDogConfiguration.objects.create(
        project=project, base_url='http"//test.com', api_key="123key"
    )

    audit_log = AuditLog(project=project, log="Some audit log")
    audit_log2 = AuditLog(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.ENVIRONMENT.name,
    )

    # When
    audit_log.save()
    audit_log2.save()

    # Then
    datadog_mock.track_event_async.assert_not_called()


@pytest.mark.parametrize(
    "use_custom_source, expected_additional_data",
    [(False, {}), (True, {"source_type_name": "flagsmith"})],
)
def test_audit_log_save__datadog_configured_with_correct_type__calls_track_event(
    project: Project,
    mocker: MockerFixture,
    use_custom_source: bool,
    expected_additional_data: dict[str, str],
) -> None:
    # Given
    requests_session_mock = mocker.patch(
        "integrations.datadog.datadog.requests.Session"
    ).return_value

    DataDogConfiguration.objects.create(
        project=project,
        base_url="http://test.com",
        api_key="123key",
        use_custom_source=use_custom_source,
    )

    # When
    AuditLog.objects.create(
        project=project,
        log="Some audit log for feature",
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    AuditLog.objects.create(
        project=project,
        log="Some audit log for feature state",
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
    )
    AuditLog.objects.create(
        project=project,
        log="Some audit log for segment",
        related_object_type=RelatedObjectType.SEGMENT.name,
    )

    # Then
    assert requests_session_mock.post.call_args_list == [
        mocker.call(
            "http://test.com/api/v1/events?api_key=123key",
            data=json.dumps(
                {
                    "text": "Some audit log for feature by user system",
                    "title": "Flagsmith Feature Flag Event",
                    "tags": ["env:unknown"],
                    **expected_additional_data,
                }
            ),
        ),
        mocker.call(
            "http://test.com/api/v1/events?api_key=123key",
            data=json.dumps(
                {
                    "text": "Some audit log for feature state by user system",
                    "title": "Flagsmith Feature Flag Event",
                    "tags": ["env:unknown"],
                    **expected_additional_data,
                }
            ),
        ),
        mocker.call(
            "http://test.com/api/v1/events?api_key=123key",
            data=json.dumps(
                {
                    "text": "Some audit log for segment by user system",
                    "title": "Flagsmith Feature Flag Event",
                    "tags": ["env:unknown"],
                    **expected_additional_data,
                }
            ),
        ),
    ]


def test_audit_log_get_history_record_model_class__valid_class_path__returns_class(
    mocker,
):  # type: ignore[no-untyped-def]
    # Given
    module_name = "module"

    mocked_import_module = mocker.patch("audit.models.import_module")

    class DummyHistoricalRecordModel:
        pass

    class_path = f"{module_name}.{DummyHistoricalRecordModel.__name__}"

    def import_module_side_effect(m):  # type: ignore[no-untyped-def]
        if m == module_name:
            return mocker.MagicMock(
                **{DummyHistoricalRecordModel.__name__: DummyHistoricalRecordModel}
            )

        raise ImportError()

    mocked_import_module.side_effect = import_module_side_effect

    # When
    klass = AuditLog.get_history_record_model_class(class_path)

    # Then
    assert klass == DummyHistoricalRecordModel  # type: ignore[comparison-overlap]


def test_audit_log_history_record__valid_history_record_id__returns_model(mocker):  # type: ignore[no-untyped-def]
    # Given
    module_name = "app.models"
    model_class_name = "MyModel"

    audit_log = AuditLog(
        history_record_id=1,
        history_record_class_path=f"{module_name}.{model_class_name}",
    )

    # Since we're using a lot of mocking here, I am explaining the setup.
    # In summary, here we are simulating a django model existing at app.models.MyModel. We mock the
    # import_module function to return another magic mock which has the MyModel attribute. Then we're
    # mocking the django ORM to get a mock model object returned at the end of it that we can use
    # in our assertions below.
    mocked_model = mocker.MagicMock()
    mocked_model_class = mocker.MagicMock()
    mocked_module = mocker.MagicMock(**{model_class_name: mocked_model_class})
    mocker.patch("audit.models.import_module", return_value=mocked_module)
    mocked_model_class.objects.filter.return_value.first.return_value = mocked_model

    # When
    record = audit_log.history_record

    # Then
    assert record == mocked_model
    mocked_model_class.objects.filter.assert_called_once_with(
        history_id=audit_log.history_record_id
    )


def test_audit_log_history_record__no_history_record_set__returns_none(mocker):  # type: ignore[no-untyped-def]
    # Given
    audit_log = AuditLog()

    # When
    record = audit_log.history_record

    # Then
    assert record is None


def test_audit_log_save__environment_set_without_project__sets_project_from_environment(
    environment,
):  # type: ignore[no-untyped-def]
    # Given
    audit_log = AuditLog(environment=environment)

    # When
    audit_log.save()

    # Then
    assert audit_log.project == environment.project


def test_audit_log_save__environment_provided__creates_process_environment_update_task(  # type: ignore[no-untyped-def]
    environment, mocker
):
    # Given
    process_environment_update = mocker.patch(
        "environments.tasks.process_environment_update"
    )

    # When
    audit_log = AuditLog.objects.create(environment=environment)

    # Then
    process_environment_update.delay.assert_called_once_with(args=(audit_log.id,))

    # and
    environment.refresh_from_db()
    assert environment.updated_at == audit_log.created_date


def test_audit_log_save__change_request_type__does_not_trigger_process_environment_update(  # type: ignore[no-untyped-def]  # noqa: E501
    environment, mocker, project
):
    # Given
    process_environment_update = mocker.patch(
        "environments.tasks.process_environment_update"
    )

    # When
    audit_log = AuditLog.objects.create(
        project=project,
        related_object_type=RelatedObjectType.CHANGE_REQUEST.name,
    )

    # Then
    process_environment_update.delay.assert_not_called()
    assert audit_log.created_date != environment.updated_at


@pytest.mark.django_db
def test_audit_log_organisation__empty_instance__returns_none() -> None:
    # Given
    audit_log = AuditLog.objects.create()

    # When
    organisation = audit_log.organisation

    # Then
    assert organisation is None
