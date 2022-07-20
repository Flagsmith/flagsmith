import time
import uuid
from threading import Thread

from django import db
from django.db import transaction
from django.test.testcases import TransactionTestCase

from organisations.models import Organisation
from task_processor.models import Task, TaskResult, TaskRun
from task_processor.processor import get_available_tasks, run_task


def _create_organisation(name: str):
    """function used to test that task is being run successfully"""
    Organisation.objects.create(name=name)


def _raise_exception():
    raise Exception()


def _hold_available_task(seconds: int = 2):
    with transaction.atomic():
        get_available_tasks().first()
        time.sleep(seconds)
        db.connections.close_all()


def test_run_task_runs_task_and_creates_task_run_object_when_success(db):
    # Given
    organisation_name = f"test-org-{uuid.uuid4()}"
    task = Task.create(_create_organisation, organisation_name)
    task.save()

    # When
    run_task(get_available_tasks())

    # Then
    assert Organisation.objects.filter(name=organisation_name).exists()

    assert TaskRun.objects.filter(task=task).count() == 1
    task_run = TaskRun.objects.get(task=task)
    assert TaskResult[task_run.result] == TaskResult.SUCCESS
    assert task_run.started_at
    assert task_run.finished_at
    assert task_run.error_details is None


def test_run_task_runs_task_and_creates_task_run_object_when_failure(db):
    # Given
    task = Task.create(_raise_exception)
    task.save()

    # When
    run_task(get_available_tasks())

    # Then
    assert TaskRun.objects.filter(task=task).count() == 1
    task_run = TaskRun.objects.get(task=task)
    assert TaskResult[task_run.result] == TaskResult.FAILURE
    assert task_run.started_at
    assert task_run.finished_at is None
    assert task_run.error_details is not None


def test_get_available_tasks_returns_empty_queryset_if_no_tasks(db):
    assert not get_available_tasks().exists()


def test_get_next_task_returns_scheduled_tasks_in_correct_order(db):
    # Given
    # 2 tasks
    task_1 = Task.create(_create_organisation, "task 1 organisation")
    task_1.save()

    task_2 = Task.create(_create_organisation, "task 2 organisation")
    task_2.save()

    # When
    available_tasks = get_available_tasks()

    # Then
    assert available_tasks[0] == task_1
    assert available_tasks[1] == task_2


class TestProcessor(TransactionTestCase):
    def test_get_next_task_skips_locked_rows(self):
        # Given
        # 2 tasks
        task_1 = Task.create(_create_organisation, "task 1 organisation")
        task_1.save()

        task_2 = Task.create(_create_organisation, "task 2 organisation")
        task_2.save()

        threads = []

        # When
        hold_first_task_thread = Thread(target=_hold_available_task)
        threads.append(hold_first_task_thread)
        hold_first_task_thread.start()

        with transaction.atomic():
            time.sleep(1)  # wait for the thread to start and hold the task
            second_task = get_available_tasks().first()

            # Then
            assert second_task == task_2

        [t.join() for t in threads]
