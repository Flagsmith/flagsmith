from task_processor.decorators import register_task_handler
from task_processor.models import Task


@register_task_handler()
def my_callable(arg_one: str, arg_two: str = None):
    """Example callable to use for tasks (needs to be global for registering to work)"""
    return arg_one, arg_two


def test_task_run():
    # Given
    args = ["foo"]
    kwargs = {"arg_two": "bar"}

    task = Task.create(my_callable.task_identifier, *args, **kwargs)

    # When
    result = task.run()

    # Then
    assert result == my_callable(*args, **kwargs)
