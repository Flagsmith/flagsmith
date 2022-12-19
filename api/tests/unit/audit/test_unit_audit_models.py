from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from integrations.datadog.models import DataDogConfiguration


def test_organisation_webhooks_are_called_when_audit_log_saved(project, mocker):
    # Given
    mock_call_webhooks = mocker.patch("audit.signals.call_organisation_webhooks")

    audit_log = AuditLog(project=project, log="Some audit log")

    # When
    audit_log.save()

    # Then
    mock_call_webhooks.assert_called()


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
