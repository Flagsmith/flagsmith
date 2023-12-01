from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from task_processor.statistics import TaskQueueStatistics


def test_task_processor_monitoring(
    admin_client: APIClient, mocker: MockerFixture
) -> None:
    # Given
    statistics = TaskQueueStatistics(waiting=1, stuck=2, in_flight=3)
    mocker.patch(
        "task_processor.views.get_task_queue_statistics", return_value=statistics
    )

    url = reverse("task_processor:monitoring")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "waiting": 1,
        "stuck": 2,
        "in_flight": 3,
    }
