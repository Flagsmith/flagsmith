import json
from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from django_capture_on_commit_callbacks import capture_on_commit_callbacks
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.exceptions import InvalidArgumentsError
from task_processor.models import RecurringTask, Task, TaskPriority
from task_processor.task_registry import get_task
from task_processor.task_run_method import TaskRunMethod
from tests.unit.task_processor.conftest import GetTaskProcessorCaplog


@pytest.fixture
def mock_thread_class(
    mocker: MockerFixture,
) -> MagicMock:
    mock_thread_class = mocker.patch(
        "task_processor.decorators.Thread",
        return_value=mocker.MagicMock(),
    )
    return mock_thread_class


@pytest.mark.django_db
def test_register_task_handler_run_in_thread__transaction_commit__true__default(
    get_task_processor_caplog: GetTaskProcessorCaplog,
    mock_thread_class: MagicMock,
) -> None:
    # Given
    caplog = get_task_processor_caplog()

    @register_task_handler()
    def my_function(*args: str, **kwargs: str) -> None:
        pass

    mock_thread = mock_thread_class.return_value

    args = ("foo",)
    kwargs = {"bar": "baz"}

    # When
    # TODO Switch to pytest-django's django_capture_on_commit_callbacks
    # fixture when migrating to Django 4
    with capture_on_commit_callbacks(execute=True):
        my_function.run_in_thread(args=args, kwargs=kwargs)

    # Then
    mock_thread_class.assert_called_once_with(
        target=my_function.unwrapped, args=args, kwargs=kwargs, daemon=True
    )
    mock_thread.start.assert_called_once()

    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message == "Running function my_function in unmanaged thread."
    )


def test_register_task_handler_run_in_thread__transaction_commit__false(
    get_task_processor_caplog: GetTaskProcessorCaplog,
    mock_thread_class: MagicMock,
) -> None:
    # Given
    caplog = get_task_processor_caplog()

    @register_task_handler(transaction_on_commit=False)
    def my_function(*args, **kwargs):
        pass

    mock_thread = mock_thread_class.return_value

    args = ("foo",)
    kwargs = {"bar": "baz"}

    # When
    my_function.run_in_thread(args=args, kwargs=kwargs)

    # Then
    mock_thread_class.assert_called_once_with(
        target=my_function.unwrapped, args=args, kwargs=kwargs, daemon=True
    )
    mock_thread.start.assert_called_once()

    assert len(caplog.records) == 1
    assert (
        caplog.records[0].message == "Running function my_function in unmanaged thread."
    )


def test_register_recurring_task(mocker, db, run_by_processor):
    # Given
    task_kwargs = {"first_arg": "foo", "second_arg": "bar"}
    run_every = timedelta(minutes=10)
    task_identifier = "test_unit_task_processor_decorators.a_function"

    # When
    @register_recurring_task(
        run_every=run_every,
        kwargs=task_kwargs,
    )
    def a_function(first_arg, second_arg):
        return first_arg + second_arg

    # Then
    task = RecurringTask.objects.get(task_identifier=task_identifier)
    assert task.serialized_kwargs == json.dumps(task_kwargs)
    assert task.run_every == run_every

    assert get_task(task_identifier)
    assert task.run() == "foobar"


def test_register_recurring_task_does_nothing_if_not_run_by_processor(mocker, db):
    # Given

    task_kwargs = {"first_arg": "foo", "second_arg": "bar"}
    run_every = timedelta(minutes=10)
    task_identifier = "test_unit_task_processor_decorators.some_function"

    # When
    @register_recurring_task(
        run_every=run_every,
        kwargs=task_kwargs,
    )
    def some_function(first_arg, second_arg):
        return first_arg + second_arg

    # Then
    assert not RecurringTask.objects.filter(task_identifier=task_identifier).exists()
    with pytest.raises(KeyError):
        assert get_task(task_identifier)


def test_register_task_handler_validates_inputs() -> None:
    # Given
    @register_task_handler()
    def my_function(*args, **kwargs):
        pass

    class NonSerializableObj:
        pass

    # When
    with pytest.raises(InvalidArgumentsError):
        my_function(NonSerializableObj())


@pytest.mark.parametrize(
    "task_run_method", (TaskRunMethod.SEPARATE_THREAD, TaskRunMethod.SYNCHRONOUSLY)
)
def test_inputs_are_validated_when_run_without_task_processor(
    settings: SettingsWrapper, task_run_method: TaskRunMethod
) -> None:
    # Given
    settings.TASK_RUN_METHOD = task_run_method

    @register_task_handler()
    def my_function(*args, **kwargs):
        pass

    class NonSerializableObj:
        pass

    # When
    with pytest.raises(InvalidArgumentsError):
        my_function.delay(args=(NonSerializableObj(),))


def test_delay_returns_none_if_task_queue_is_full(settings, db):
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

    @register_task_handler(queue_size=1)
    def my_function(*args, **kwargs):
        pass

    for _ in range(10):
        Task.objects.create(
            task_identifier="test_unit_task_processor_decorators.my_function"
        )

    # When
    task = my_function.delay()

    # Then
    assert task is None


def test_can_create_task_with_priority(settings, db):
    # Given
    settings.TASK_RUN_METHOD = TaskRunMethod.TASK_PROCESSOR

    @register_task_handler(priority=TaskPriority.HIGH)
    def my_function(*args, **kwargs):
        pass

    for _ in range(10):
        Task.objects.create(
            task_identifier="test_unit_task_processor_decorators.my_function"
        )

    # When
    task = my_function.delay()

    # Then
    assert task.priority == TaskPriority.HIGH
