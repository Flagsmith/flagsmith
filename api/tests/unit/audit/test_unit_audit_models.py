from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from audit.serializers import AuditLogListSerializer
from integrations.datadog.models import DataDogConfiguration
from organisations.models import Organisation, OrganisationWebhook
from projects.models import Project
from webhooks.webhooks import WebhookEventType


def test_organisation_webhooks_are_called_when_audit_log_saved(
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


def test_data_dog_track_event_not_called_on_audit_log_saved_when_not_configured(
    project, mocker
):
    # Given Audit log and project not configured for Datadog
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )
    audit_log = AuditLog(project=project, log="Some audit log")

    # When Audit log saved
    audit_log.save()

    # Then datadog track even should not be triggered
    datadog_mock.track_event_async.assert_not_called()


def test_data_dog_track_event_not_called_on_audit_log_saved_when_wrong(mocker, project):
    # Given Audit log and project configured for Datadog integration
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

    # When Audit log saved with wrong types
    audit_log.save()
    audit_log2.save()

    # Then datadog track event should not be triggered
    datadog_mock.track_event_async.assert_not_called()


def test_data_dog_track_event_called_on_audit_log_saved_when_correct_type(
    project, mocker
):
    # Given project configured for Datadog integration
    datadog_mock = mocker.patch(
        "integrations.datadog.datadog.DataDogWrapper.track_event_async"
    )

    DataDogConfiguration.objects.create(
        project=project, base_url='http"//test.com', api_key="123key"
    )

    # When Audit logs created with correct type
    AuditLog.objects.create(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.FEATURE.name,
    )
    AuditLog.objects.create(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
    )
    AuditLog.objects.create(
        project=project,
        log="Some audit log",
        related_object_type=RelatedObjectType.SEGMENT.name,
    )

    # Then datadog track even triggered for each AuditLog
    assert 3 == datadog_mock.call_count


def test_audit_log_get_history_record_model_class(mocker):
    # Given
    module_name = "module"

    mocked_import_module = mocker.patch("audit.models.import_module")

    class DummyHistoricalRecordModel:
        pass

    class_path = f"{module_name}.{DummyHistoricalRecordModel.__name__}"

    def import_module_side_effect(m):
        if m == module_name:
            return mocker.MagicMock(
                **{DummyHistoricalRecordModel.__name__: DummyHistoricalRecordModel}
            )

        raise ImportError()

    mocked_import_module.side_effect = import_module_side_effect

    # When
    klass = AuditLog.get_history_record_model_class(class_path)

    # Then
    assert klass == DummyHistoricalRecordModel


def test_audit_log_history_record(mocker):
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


def test_audit_log_history_record_for_audit_log_record_with_no_history_record(mocker):
    # Given
    audit_log = AuditLog()

    # When
    record = audit_log.history_record

    # Then
    assert record is None


def test_audit_log_save_project_is_added_if_not_set(environment):
    # Given
    audit_log = AuditLog(environment=environment)

    # When
    audit_log.save()

    # Then
    assert audit_log.project == environment.project


def test_creating_audit_logs_creates_process_environment_update_task(
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


def test_creating_audit_logs_for_change_request_does_not_trigger_process_environment_update(
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
