import logging
import typing

import pytest


@pytest.fixture
def run_by_processor(monkeypatch):
    monkeypatch.setenv("RUN_BY_PROCESSOR", "True")


class GetTaskProcessorCaplog(typing.Protocol):
    def __call__(
        self, log_level: str | int = logging.INFO
    ) -> pytest.LogCaptureFixture: ...


@pytest.fixture
def get_task_processor_caplog(
    caplog: pytest.LogCaptureFixture,
) -> GetTaskProcessorCaplog:
    # caplog doesn't allow you to capture logging outputs from loggers that don't
    # propagate to root. Quick hack here to get the task_processor logger to
    # propagate.
    # TODO: look into using loguru.

    def _inner(log_level: str | int = logging.INFO) -> pytest.LogCaptureFixture:
        task_processor_logger = logging.getLogger("task_processor")
        task_processor_logger.propagate = True
        # Assume required level for the logger.
        task_processor_logger.setLevel(log_level)
        caplog.set_level(log_level)
        return caplog

    return _inner
