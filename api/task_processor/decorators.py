import logging
import os
import typing
from datetime import datetime, time, timedelta
from inspect import getmodule
from threading import Thread

from django.conf import settings
from django.utils import timezone

from task_processor.exceptions import InvalidArgumentsError
from task_processor.models import RecurringTask, Task
from task_processor.task_registry import register_task
from task_processor.task_run_method import TaskRunMethod

logger = logging.getLogger(__name__)


def register_task_handler(task_name: str = None):
    def decorator(f: typing.Callable):
        nonlocal task_name

        task_name = task_name or f.__name__
        task_module = getmodule(f).__name__.rsplit(".")[-1]
        task_identifier = f"{task_module}.{task_name}"
        register_task(task_identifier, f)

        def delay(
            *,
            delay_until: datetime = None,
            args: typing.Tuple = (),
            kwargs: typing.Dict = None,
        ) -> typing.Optional[Task]:
            logger.debug("Request to run task '%s' asynchronously.", task_identifier)

            kwargs = kwargs or dict()

            if delay_until and settings.TASK_RUN_METHOD != TaskRunMethod.TASK_PROCESSOR:
                logger.warning(
                    "Cannot schedule tasks to run in the future without task processor."
                )
                return

            if settings.TASK_RUN_METHOD == TaskRunMethod.SYNCHRONOUSLY:
                _validate_inputs(*args, **kwargs)
                f(*args, **kwargs)
            elif settings.TASK_RUN_METHOD == TaskRunMethod.SEPARATE_THREAD:
                logger.debug("Running task '%s' in separate thread", task_identifier)
                run_in_thread(args=args, kwargs=kwargs)
            else:
                logger.debug("Creating task for function '%s'...", task_identifier)
                task = Task.schedule_task(
                    schedule_for=delay_until or timezone.now(),
                    task_identifier=task_identifier,
                    args=args,
                    kwargs=kwargs,
                )
                task.save()
                return task

        def run_in_thread(*, args: typing.Tuple = (), kwargs: typing.Dict = None):
            logger.info("Running function %s in unmanaged thread.", f.__name__)
            _validate_inputs(*args, **kwargs)
            Thread(target=f, args=args, kwargs=kwargs, daemon=True).start()

        def _wrapper(*args, **kwargs):
            """
            Execute the function after validating the arguments. Ensures that, in unit testing,
            the arguments are validated to prevent issues with serialization in an environment
            that utilises the task processor.
            """
            _validate_inputs(*args, **kwargs)
            return f(*args, **kwargs)

        _wrapper.delay = delay
        _wrapper.run_in_thread = run_in_thread
        _wrapper.task_identifier = task_identifier

        # patch the original unwrapped function onto the wrapped version for testing
        _wrapper.unwrapped = f

        return _wrapper

    return decorator


def register_recurring_task(
    run_every: timedelta,
    task_name: str = None,
    args: typing.Tuple = (),
    kwargs: typing.Dict = None,
    first_run_time: time = None,
):
    if not os.environ.get("RUN_BY_PROCESSOR"):
        # Do not register recurring tasks if not invoked by task processor
        return lambda f: f

    def decorator(f: typing.Callable):
        nonlocal task_name

        task_name = task_name or f.__name__
        task_module = getmodule(f).__name__.rsplit(".")[-1]
        task_identifier = f"{task_module}.{task_name}"

        register_task(task_identifier, f)

        task, _ = RecurringTask.objects.update_or_create(
            task_identifier=task_identifier,
            defaults={
                "serialized_args": RecurringTask.serialize_data(args or tuple()),
                "serialized_kwargs": RecurringTask.serialize_data(kwargs or dict()),
                "run_every": run_every,
                "first_run_time": first_run_time,
            },
        )
        return task

    return decorator


def _validate_inputs(*args, **kwargs):
    try:
        Task.serialize_data(args or tuple())
        Task.serialize_data(kwargs or dict())
    except TypeError as e:
        raise InvalidArgumentsError("Inputs are not serializable.") from e
