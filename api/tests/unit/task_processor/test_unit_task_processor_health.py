from task_processor.health import check_processor_health
from task_processor.models import HealthCheckModel


def test_check_processor_health_returns_false_if_task_not_processed(mocker):
    # Given
    mocker.patch("task_processor.health.create_health_check_model")
    mocked_health_check_model_class = mocker.patch(
        "task_processor.health.HealthCheckModel"
    )
    mocked_health_check_model_class.objects.filter.return_value.first.return_value = (
        None
    )

    # When
    result = check_processor_health(max_tries=3)

    # Then
    assert result is False


def test_check_processor_health_returns_true_if_task_processed(db, settings):
    # Given
    settings.RUN_TASKS_SYNCHRONOUSLY = True

    # When
    result = check_processor_health(max_tries=3)

    # Then
    # the health is reported as success
    assert result is True

    # but the health check model used to verify the health is deleted
    assert not HealthCheckModel.objects.exists()
