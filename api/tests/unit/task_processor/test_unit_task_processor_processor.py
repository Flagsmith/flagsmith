import time
import uuid
from threading import Thread

from django.db import transaction
from django.test.testcases import TransactionTestCase

from organisations.models import Organisation
from task_processor.decorators import register_task_handler
from task_processor.models import Task, TaskResult, TaskRun
from task_processor.processor import run_next_task


def test_run_task_runs_task_and_creates_task_run_object_when_success(db):
    # Given
    organisation_name = f"test-org-{uuid.uuid4()}"
    task = Task.create(_create_organisation.task_identifier, organisation_name)
    task.save()

    # When
    task_run = run_next_task()

    # Then
    assert Organisation.objects.filter(name=organisation_name).exists()

    assert TaskRun.objects.filter(task=task).count() == 1
    assert task_run.result == TaskResult.SUCCESS
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None

    task.refresh_from_db()
    assert task.completed


def test_run_task_runs_task_and_creates_task_run_object_when_failure(db):
    # Given
    task = Task.create(_raise_exception.task_identifier)
    task.save()

    # When
    task_run = run_next_task()

    # Then
    assert TaskRun.objects.filter(task=task).count() == 1
    assert task_run.result == TaskResult.FAILURE
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None

    task.refresh_from_db()
    assert not task.completed


def test_run_next_task_does_nothing_if_no_tasks(db):
    # Given - no tasks
    # When
    result = run_next_task()
    # Then
    assert result is None
    assert not TaskRun.objects.exists()


def test_run_next_task_runs_tasks_in_correct_order(db):
    # Given
    # 2 tasks
    task_1 = Task.create(_create_organisation.task_identifier, "task 1 organisation")
    task_1.save()

    task_2 = Task.create(_create_organisation.task_identifier, "task 2 organisation")
    task_2.save()

    # When
    task_run_1 = run_next_task()
    task_run_2 = run_next_task()

    # Then
    assert task_run_1.task == task_1
    assert task_run_2.task == task_2


class TestProcessor(TransactionTestCase):
    def test_get_next_task_skips_locked_rows(self):
        """
        This test verifies that tasks are locked while being executed, and hence
        new task runners are not able to pick up 'in progress' tasks.
        """
        # Given
        # 2 tasks
        # One which is configured to just sleep for 3 seconds, to simulate a task
        # being held for a short period of time
        task_1 = Task.create(_sleep.task_identifier, 3)
        task_1.save()

        # and another which should create an organisation
        task_2 = Task.create(
            _create_organisation.task_identifier, "task 2 organisation"
        )
        task_2.save()

        threads = []

        # When
        # we spawn a new thread to run the first task (configured to just sleep)
        task_runner_thread = Thread(target=run_next_task)
        threads.append(task_runner_thread)
        task_runner_thread.start()

        with transaction.atomic():
            # and subsequently attempt to run another task in the main thread
            time.sleep(1)  # wait for the thread to start and hold the task
            task_run = run_next_task()

            # Then
            # the second task is run while the 1st task is held
            assert task_run.task == task_2

        [t.join() for t in threads]


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
