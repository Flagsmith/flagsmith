from decimal import Decimal

import pytest

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

    task = Task.create(my_callable.task_identifier, args=args, kwargs=kwargs)

    # When
    result = task.run()

    # Then
    assert result == my_callable(*args, **kwargs)


@pytest.mark.parametrize(
    "input, expected_output",
    (
        ({"value": Decimal("10")}, '{"value": 10}'),
        ({"value": Decimal("10.12345")}, '{"value": 10.12345}'),
    ),
)
def test_serialize_data_handles_decimal_objects(input, expected_output):
    assert Task.serialize_data(input) == expected_output
