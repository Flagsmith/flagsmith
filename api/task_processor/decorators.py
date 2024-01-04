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

P = typing.ParamSpec("P")

logger = logging.getLogger(__name__)


class TaskHandler(typing.Generic[P]):
    __slots__ = (
        "unwrapped",
        "queue_size",
        "priority",
        "transaction_on_commit",
        "task_identifier",
    )

    unwrapped: typing.Callable[P, None]

    def __init__(
        self,
        f: typing.Callable[P, None],
        *,
        task_name: str | None = None,
        queue_size: int | None = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        transaction_on_commit: bool = True,
    ) -> None:
        self.unwrapped = f
        self.queue_size = queue_size
        self.priority = priority
        self.transaction_on_commit = transaction_on_commit

        task_name = task_name or f.__name__
        task_module = getmodule(f).__name__.rsplit(".")[-1]
        self.task_identifier = task_identifier = f"{task_module}.{task_name}"
        register_task(task_identifier, f)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        _validate_inputs(*args, **kwargs)
        return self.unwrapped(*args, **kwargs)

    def delay(
        self,
        *,
        delay_until: datetime | None = None,
        # TODO @khvn26 consider typing `args` and `kwargs` with `ParamSpec`
        # (will require a change to the signature)
        args: tuple[typing.Any, ...] = (),
        kwargs: dict[str, typing.Any] | None = None,
    ) -> Task | None:
        logger.debug("Request to run task '%s' asynchronously.", self.task_identifier)

        kwargs = kwargs or {}

        if delay_until and settings.TASK_RUN_METHOD != TaskRunMethod.TASK_PROCESSOR:
            logger.warning(
                "Cannot schedule tasks to run in the future without task processor."
            )
            return

        if settings.TASK_RUN_METHOD == TaskRunMethod.SYNCHRONOUSLY:
            _validate_inputs(*args, **kwargs)
            self.unwrapped(*args, **kwargs)
        elif settings.TASK_RUN_METHOD == TaskRunMethod.SEPARATE_THREAD:
            logger.debug("Running task '%s' in separate thread", self.task_identifier)
            self.run_in_thread(args=args, kwargs=kwargs)
        else:
            logger.debug("Creating task for function '%s'...", self.task_identifier)
            try:
                task = Task.create(
                    task_identifier=self.task_identifier,
                    scheduled_for=delay_until or timezone.now(),
                    priority=self.priority,
                    queue_size=self.queue_size,
                    args=args,
                    kwargs=kwargs,
                )
            except TaskQueueFullError as e:
                logger.warning(e)
                return

            task.save()
            return task

    def run_in_thread(
        self,
        *,
        args: tuple[typing.Any] = (),
        kwargs: dict[str, typing.Any] | None = None,
    ) -> None:
        _validate_inputs(*args, **kwargs)
        thread = Thread(target=self.unwrapped, args=args, kwargs=kwargs, daemon=True)

        def _start() -> None:
            logger.info(
                "Running function %s in unmanaged thread.", self.unwrapped.__name__
            )
            thread.start()

        if self.transaction_on_commit:
            return on_commit(_start)
        return _start()


def register_task_handler(  # noqa: C901
    *,
    task_name: str | None = None,
    queue_size: int | None = None,
    priority: TaskPriority = TaskPriority.NORMAL,
    transaction_on_commit: bool = True,
) -> typing.Callable[[typing.Callable[P, None]], TaskHandler[P]]:
    """
    Turn a function into an asynchronous task.

    :param str task_name: task name. Defaults to function name.
    :param int queue_size: (`TASK_PROCESSOR` task run method only)
        max queue size for the task. Task runs exceeding the max size get dropped by
        the task processor Defaults to `None` (infinite).
    :param TaskPriority priority: task priority.
    :param bool transaction_on_commit: (`SEPARATE_THREAD` task run method only)
        Whether to wrap the task call in `transanction.on_commit`. Defaults to `True`.
        We need this for the task to be able to access data committed with the current
        transaction. If the task is invoked outside of a transaction, it will start
        immediately.
        Pass `False` if you want the task to start immediately regardless of current
        transaction.
    :rtype: TaskHandler
    """

    def wrapper(f: typing.Callable[P, None]) -> TaskHandler[P]:
        return TaskHandler(
            f,
            task_name=task_name,
            queue_size=queue_size,
            priority=priority,
            transaction_on_commit=transaction_on_commit,
        )

    return wrapper


def register_recurring_task(
    run_every: timedelta,
    task_name: str | None = None,
    args: tuple[typing.Any] = (),
    kwargs: dict[str, typing.Any] | None = None,
    first_run_time: time | None = None,
) -> typing.Callable[[typing.Callable[..., None]], RecurringTask]:
    if not os.environ.get("RUN_BY_PROCESSOR"):
        # Do not register recurring tasks if not invoked by task processor
        return lambda f: f

    def decorator(f: typing.Callable[..., None]) -> RecurringTask:
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
