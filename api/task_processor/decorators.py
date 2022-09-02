import logging
import typing
from datetime import datetime
from inspect import getmodule
from threading import Thread

from django.conf import settings
from django.utils import timezone

from task_processor.models import Task
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
            args: typing.Tuple = None,
            kwargs: typing.Dict = None,
        ) -> typing.Optional[Task]:
            args = args or tuple()
            kwargs = kwargs or dict()

            if delay_until and settings.TASK_RUN_METHOD != TaskRunMethod.TASK_PROCESSOR:
                logger.warning(
                    "Cannot schedule tasks to run in the future without task processor."
                )
                return

            if settings.TASK_RUN_METHOD == TaskRunMethod.SYNCHRONOUSLY:
                logger.debug("Running task '%s' synchronously", task_identifier)
                f(*args, **kwargs)
            elif settings.TASK_RUN_METHOD == TaskRunMethod.SEPARATE_THREAD:
                logger.debug("Running task '%s' in separate thread", task_identifier)
                run_in_thread(*args, **kwargs)
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

        def run_in_thread(*args, **kwargs):
            logger.info("Running function %s in unmanaged thread.", f.__name__)
            Thread(target=f, args=args, kwargs=kwargs, daemon=True).start()

        f.delay = delay
        f.run_in_thread = run_in_thread
        f.task_identifier = task_identifier

        return f

    return decorator
