import logging
import os
import typing
from datetime import datetime, time, timedelta
from inspect import getmodule
from threading import Thread

from django.conf import settings
from django.db.transaction import on_commit
from django.utils import timezone

from task_processor.exceptions import InvalidArgumentsError, TaskQueueFullError
from task_processor.models import RecurringTask, Task, TaskPriority
from task_processor.task_registry import register_task
from task_processor.task_run_method import TaskRunMethod

logger = logging.getLogger(__name__)

W = typing.TypeVar("W")
P = typing.ParamSpec("P")
WrappedFunction = typing.Callable[P, None]


class TaskHandler(typing.Generic[W]):
    task_identifier: str
    unwrapped: W

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        ...

    # TODO @khvn26 Consider typing `delay` and `run_in_thread` using `ParamSpec`.
    # This will require a change to methods' signatures.

    def delay(
        self,
        *,
        delay_until: datetime | None = None,
        args: tuple[typing.Any] = (),
        kwargs: dict[str, typing.Any] | None = None,
    ) -> Task | None:
        ...

    def run_in_thread(
        *,
        args: tuple[typing.Any] = (),
        kwargs: dict[str, typing.Any] | None = None,
    ) -> None:
        ...


def register_task_handler(  # noqa: C901
    *,
    task_name: str | None = None,
    queue_size: int | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    transaction_on_commit: bool = True,
) -> typing.Callable[[W], TaskHandler[W]]:
    """
    Turn a function into an asynchronous task.

    :param str task_name: task name. Defaults to function name.
    :param int queue_size: (`TASK_PROCESSOR` task run method only)
        max queue size for the task. Task runs exceeding the max size get dropped by
        the task processor Defaults to `None` (infinite).
    :param TaskPriority priority: task priority.
    :param bool transaction_on_commit: (`SEPARATE_THREAD` task run method only)
        Whether to wrap the task call in `transanction.on_commit`. Defaults to `True`.
    :rtype: TaskProtocol
    """

    def decorator(f: W) -> TaskHandler[W]:
        nonlocal task_name, transaction_on_commit

        task_name = task_name or f.__name__
        task_module = getmodule(f).__name__.rsplit(".")[-1]
        task_identifier = f"{task_module}.{task_name}"
        register_task(task_identifier, f)

        def delay(
            *,
            delay_until: datetime | None = None,
            args: tuple[typing.Any] = (),
            kwargs: dict[str, typing.Any] | None = None,
        ) -> Task | None:
            logger.debug("Request to run task '%s' asynchronously.", task_identifier)

            kwargs = kwargs or {}

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
                try:
                    task = Task.create(
                        task_identifier=task_identifier,
                        scheduled_for=delay_until or timezone.now(),
                        priority=priority,
                        queue_size=queue_size,
                        args=args,
                        kwargs=kwargs,
                    )
                except TaskQueueFullError as e:
                    logger.warning(e)
                    return

                task.save()
                return task

        def run_in_thread(
            *,
            args: tuple[typing.Any] = (),
            kwargs: dict[str, typing.Any] | None = None,
        ) -> None:
            logger.info("Running function %s in unmanaged thread.", f.__name__)
            _validate_inputs(*args, **kwargs)
            thread = Thread(target=f, args=args, kwargs=kwargs, daemon=True)
            if transaction_on_commit:
                return on_commit(thread.start)
            return thread.start()

        def _wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
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
    task_name: str | None = None,
    args: tuple[typing.Any] = (),
    kwargs: dict[str, typing.Any] | None = None,
    first_run_time: time | None = None,
) -> typing.Callable[[WrappedFunction], RecurringTask]:
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
                "serialized_args": RecurringTask.serialize_data(args or ()),
                "serialized_kwargs": RecurringTask.serialize_data(kwargs or {}),
                "run_every": run_every,
                "first_run_time": first_run_time,
            },
        )
        return task

    return decorator


def _validate_inputs(*args: typing.Any, **kwargs: typing.Any) -> None:
    try:
        Task.serialize_data(args or ())
        Task.serialize_data(kwargs or {})
    except TypeError as e:
        raise InvalidArgumentsError("Inputs are not serializable.") from e
