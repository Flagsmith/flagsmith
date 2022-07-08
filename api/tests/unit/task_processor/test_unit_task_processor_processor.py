from task_processor.models import Task
from task_processor.processor import run_next_task

callers = set()


def _add_to_callers(caller: str):
    global callers
    callers.add(caller)


def test_run_next_task_runs_first_task(db):
    # Given
    global callers  # todo: remove need for global variable

    # 2 tasks
    task_1 = Task.create(_add_to_callers, "task 1")
    task_1.save()

    task_2 = Task.create(_add_to_callers, "task 2")
    task_2.save()

    # When
    run_next_task()

    # Then
    assert "task 1" in callers
    assert "task 2" not in callers

    callers.clear()
