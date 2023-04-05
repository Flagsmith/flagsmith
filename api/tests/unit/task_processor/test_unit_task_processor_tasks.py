from datetime import timedelta

from django.utils import timezone

from task_processor.models import Task
from task_processor.tasks import clean_up_old_tasks


def test_clean_up_old_tasks_does_nothing_when_no_tasks(db):
    # Given
    assert Task.objects.count() == 0

    # When
    clean_up_old_tasks()

    # Then
    assert Task.objects.count() == 0


def test_clean_up_old_tasks(settings, django_assert_num_queries, db):
    # Given
    now = timezone.now()
    three_days_ago = now - timedelta(days=3)
    one_day_ago = now - timedelta(days=1)
    one_hour_from_now = now + timedelta(hours=1)

    settings.TASK_RETENTION_DAYS = 2
    settings.TASK_DELETE_BATCH_SIZE = 1

    # 2 completed tasks that were scheduled before retention period
    for _ in range(2):
        Task.objects.create(
            task_identifier="some.identifier",
            scheduled_for=three_days_ago,
            completed=True,
        )

    # a task that has been completed but is within the retention period
    task_in_retention_period = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=one_day_ago, completed=True
    )

    # and a task that has yet to be completed
    future_task = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=one_hour_from_now
    )

    # and a task that failed
    failed_task = Task.objects.create(
        task_identifier="some.identifier", scheduled_for=three_days_ago, num_failures=3
    )

    # When
    with django_assert_num_queries(9):
        # We expect 9 queries to be run here since we have set the delete batch size to 1 and there are 2
        # tasks we expect it to delete. Therefore, we have 2 loops, each consisting of 4 queries:
        #  1. Check if any tasks matching the query exist
        #  2. Grab the ids of any matching tasks
        #  3. Delete all TaskRun objects for those task_id values
        #  4. Delete all Task objects for those ids
        #
        # The final (9th) query is checking if any tasks exist again (which returns false).
        clean_up_old_tasks()

    # Then
    assert list(Task.objects.all()) == [
        task_in_retention_period,
        future_task,
        failed_task,
    ]


def test_clean_up_old_tasks_include_failed_tasks(
    settings, django_assert_num_queries, db
):
    # Given
    three_days_ago = timezone.now() - timedelta(days=3)

    settings.TASK_RETENTION_DAYS = 2
    settings.TASK_DELETE_INCLUDE_FAILED_TASKS = True

    # a task that failed
    Task.objects.create(
        task_identifier="some.identifier", scheduled_for=three_days_ago, num_failures=3
    )

    # When
    clean_up_old_tasks()

    # Then
    assert not Task.objects.exists()
