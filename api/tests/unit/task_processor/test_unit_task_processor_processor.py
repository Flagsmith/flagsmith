import time
import uuid
from datetime import timedelta
from threading import Thread

from django.test.testcases import TransactionTestCase

from organisations.models import Organisation
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.models import (
    RecurringTask,
    RecurringTaskRun,
    Task,
    TaskResult,
    TaskRun,
)
from task_processor.processor import run_recurring_tasks, run_tasks
from task_processor.task_registry import registered_tasks


def test_run_task_runs_task_and_creates_task_run_object_when_success(db):
    # Given
    organisation_name = f"test-org-{uuid.uuid4()}"
    task = Task.create(_create_organisation.task_identifier, args=(organisation_name,))
    task.save()

    # When
    task_runs = run_tasks()

    # Then
    assert Organisation.objects.filter(name=organisation_name).exists()

    assert len(task_runs) == TaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None

    task.refresh_from_db()
    assert task.completed


def test_run_recurring_tasks_runs_task_and_creates_recurring_task_run_object_when_success(
    db, monkeypatch
):
    # Given
    monkeypatch.setenv("RUN_BY_PROCESSOR", "True")

    organisation_name = f"test-org-{uuid.uuid4()}"
    task_identifier = "test_unit_task_processor_processor._create_organisation"

    @register_recurring_task(run_every=timedelta(seconds=1), args=(organisation_name,))
    def _create_organisation(organisation_name):
        Organisation.objects.create(name=organisation_name)

    task = RecurringTask.objects.get(task_identifier=task_identifier)
    # When
    task_runs = run_recurring_tasks()

    # Then
    assert Organisation.objects.filter(name=organisation_name).count() == 1

    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.SUCCESS
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None


def test_run_recurring_tasks_multiple_runs(db, run_by_processor):
    # Given
    organisation_name = "test-org"
    task_identifier = "test_unit_task_processor_processor._create_organisation"

    @register_recurring_task(
        run_every=timedelta(milliseconds=100), args=(organisation_name,)
    )
    def _create_organisation(organisation_name):
        Organisation.objects.create(name=organisation_name)

    task = RecurringTask.objects.get(task_identifier=task_identifier)

    # When
    first_task_runs = run_recurring_tasks()
    time.sleep(0.2)

    second_task_runs = run_recurring_tasks()

    task_runs = first_task_runs + second_task_runs

    # Then
    assert Organisation.objects.filter(name=organisation_name).count() == 2

    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 2
    for task_run in task_runs:
        assert task_run.result == TaskResult.SUCCESS
        assert task_run.started_at
        assert task_run.finished_at
        assert task_run.error_details is None


def test_run_recurring_tasks_only_executes_tasks_and_interval_set_by_run_every(
    db, run_by_processor
):
    # Given
    organisation_name = "test-org"
    task_identifier = "test_unit_task_processor_processor._create_organisation"

    @register_recurring_task(
        run_every=timedelta(milliseconds=100), args=(organisation_name,)
    )
    def _create_organisation(organisation_name):
        Organisation.objects.create(name=organisation_name)

    task = RecurringTask.objects.get(task_identifier=task_identifier)

    # When - we call run_recurring_tasks twice
    run_recurring_tasks()
    run_recurring_tasks()

    # Then - we expect the task to have been run once

    assert Organisation.objects.filter(name=organisation_name).count() == 1

    assert RecurringTaskRun.objects.filter(task=task).count() == 1


def test_run_recurring_tasks_deletes_the_task_if_it_is_not_registered(
    db, run_by_processor
):
    # Given
    task_identifier = "test_unit_task_processor_processor._a_task"

    @register_recurring_task(run_every=timedelta(milliseconds=100))
    def _a_task():
        pass

    # now - remove the task from the registry
    registered_tasks.pop(task_identifier)

    # When
    task_runs = run_recurring_tasks()

    # Then
    assert len(task_runs) == 0
    assert not RecurringTask.objects.filter(task_identifier=task_identifier).exists()


def test_run_task_runs_task_and_creates_task_run_object_when_failure(db):
    # Given
    task = Task.create(_raise_exception.task_identifier)
    task.save()

    # When
    task_runs = run_tasks()

    # Then
    assert len(task_runs) == TaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None

    task.refresh_from_db()
    assert not task.completed


def test_run_recurring_task_runs_task_and_creates_recurring_task_run_object_when_failure(
    db, run_by_processor
):
    # Given
    task_identifier = "test_unit_task_processor_processor._raise_exception"

    @register_recurring_task(run_every=timedelta(seconds=1))
    def _raise_exception(organisation_name):
        raise RuntimeError("test exception")

    task = RecurringTask.objects.get(task_identifier=task_identifier)

    # When
    task_runs = run_recurring_tasks()

    # Then
    assert len(task_runs) == RecurringTaskRun.objects.filter(task=task).count() == 1
    task_run = task_runs[0]
    assert task_run.result == TaskResult.FAILURE
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None


def test_run_next_task_does_nothing_if_no_tasks(db):
    # Given - no tasks
    # When
    result = run_tasks()
    # Then
    assert result == []
    assert not TaskRun.objects.exists()


def test_run_next_task_runs_tasks_in_correct_order(db):
    # Given
    # 2 tasks
    task_1 = Task.create(
        _create_organisation.task_identifier, args=("task 1 organisation",)
    )
    task_1.save()

    task_2 = Task.create(
        _create_organisation.task_identifier, args=("task 2 organisation",)
    )
    task_2.save()

    # When
    task_runs_1 = run_tasks()
    task_runs_2 = run_tasks()

    # Then
    assert task_runs_1[0].task == task_1
    assert task_runs_2[0].task == task_2


class TestProcessor(TransactionTestCase):
    def test_run_tasks_skips_locked_tasks(self):
        """
        This test verifies that tasks are locked while being executed, and hence
        new task runners are not able to pick up 'in progress' tasks.
        """
        # Given
        # 2 tasks
        # One which is configured to just sleep for 3 seconds, to simulate a task
        # being held for a short period of time
        task_1 = Task.create(_sleep.task_identifier, args=(3,))
        task_1.save()

        # and another which should create an organisation
        task_2 = Task.create(
            _create_organisation.task_identifier, args=("task 2 organisation",)
        )
        task_2.save()

        # When
        # we spawn a new thread to run the first task (configured to just sleep)
        task_runner_thread = Thread(target=run_tasks)
        task_runner_thread.start()

        # and subsequently attempt to run another task in the main thread
        time.sleep(1)  # wait for the thread to start and hold the task
        task_runs = run_tasks()

        # Then
        # the second task is run while the 1st task is held
        assert task_runs[0].task == task_2

        task_runner_thread.join()


def test_run_more_than_one_task(db):
    # Given
    num_tasks = 5

    tasks = []
    for _ in range(num_tasks):
        organisation_name = f"test-org-{uuid.uuid4()}"
        tasks.append(
            Task.create(_create_organisation.task_identifier, args=(organisation_name,))
        )
    Task.objects.bulk_create(tasks)

    # When
    task_runs = run_tasks(5)

    # Then
    assert len(task_runs) == num_tasks

    for task_run in task_runs:
        assert task_run.result == TaskResult.SUCCESS
        assert task_run.started_at
        assert task_run.finished_at
        assert task_run.error_details is None

    for task in tasks:
        task.refresh_from_db()
        assert task.completed


@register_task_handler()
def _create_organisation(name: str):
    """function used to test that task is being run successfully"""
    Organisation.objects.create(name=name)


@register_task_handler()
def _raise_exception():
    raise Exception()


@register_task_handler()
def _sleep(seconds: int):
    time.sleep(seconds)
