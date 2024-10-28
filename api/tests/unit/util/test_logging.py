import json
import logging
import logging.config
import os

import pytest
from gunicorn.config import Config
from pytest_django.fixtures import SettingsWrapper

from util.logging import JsonFormatter


@pytest.mark.freeze_time("2023-12-08T06:05:47.320000+00:00")
def test_json_formatter__outputs_expected(
    inspecting_handler: logging.Handler,
    request: pytest.FixtureRequest,
) -> None:
    # Given
    json_formatter = JsonFormatter()

    inspecting_handler.setFormatter(json_formatter)
    logger = logging.getLogger("test_json_formatter__outputs_expected")
    logger.addHandler(inspecting_handler)
    logger.setLevel(logging.INFO)

    expected_pid = os.getpid()
    expected_module_path = os.path.abspath(request.path)
    expected_tb_string = (
        "Traceback (most recent call last):\n"
        f'  File "{expected_module_path}",'
        " line 37, in _log_traceback\n"
        "    raise Exception()\nException"
    )

    def _log_traceback() -> None:
        try:
            raise Exception()
        except Exception as exc:
            logger.error("this is an error", exc_info=exc)

    # When
    logger.info("hello %s, %d", "arg1", 22.22)
    _log_traceback()

    # Then
    assert [json.loads(message) for message in inspecting_handler.messages] == [
        {
            "levelname": "INFO",
            "message": "hello arg1, 22",
            "timestamp": "2023-12-08 06:05:47,319",
            "logger_name": "test_json_formatter__outputs_expected",
            "process_id": expected_pid,
            "thread_name": "MainThread",
        },
        {
            "levelname": "ERROR",
            "message": "this is an error",
            "timestamp": "2023-12-08 06:05:47,319",
            "logger_name": "test_json_formatter__outputs_expected",
            "process_id": expected_pid,
            "thread_name": "MainThread",
            "exc_info": expected_tb_string,
        },
    ]


def test_gunicorn_json_capable_logger__non_existent_setting__not_raises(
    settings: SettingsWrapper,
) -> None:
    # Given
    del settings.LOG_FORMAT
    config = Config()

    # When & Then
    from util.logging import GunicornJsonCapableLogger

    GunicornJsonCapableLogger(config)
