import json
import logging
import logging.config
import os
from datetime import datetime

import pytest
from gunicorn.config import AccessLogFormat, Config  # type: ignore[import-untyped]
from pytest_django.fixtures import SettingsWrapper

from util.logging import GunicornAccessLogJsonFormatter, JsonFormatter


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
        " line 38, in _log_traceback\n"
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
    assert [json.loads(message) for message in inspecting_handler.messages] == [  # type: ignore[attr-defined]
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


@pytest.mark.freeze_time("2023-12-08T06:05:47.320000+00:00")
def test_gunicorn_access_log_json_formatter__outputs_expected() -> None:
    # Given
    gunicorn_access_log_json_formatter = GunicornAccessLogJsonFormatter()
    log_record = logging.LogRecord(
        name="gunicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg=AccessLogFormat.default,
        args={
            "a": "requests",
            "b": "-",
            "B": None,
            "D": 1000000,
            "f": "-",
            "h": "192.168.0.1",
            "H": None,
            "l": "-",
            "L": "1.0",
            "m": "GET",
            "M": 1000,
            "p": "<42>",
            "q": "foo=bar",
            "r": "GET",
            "s": 200,
            "T": 1,
            "t": datetime.fromisoformat("2023-12-08T06:05:47.320000+00:00").strftime(
                "[%d/%b/%Y:%H:%M:%S %z]"
            ),
            "u": "-",
            "U": "/test",
        },
        exc_info=None,
    )
    expected_pid = os.getpid()

    # When
    json_log = gunicorn_access_log_json_formatter.get_json_record(log_record)

    # Then
    assert json_log == {
        "duration_in_ms": 1000,
        "levelname": "INFO",
        "logger_name": "gunicorn.access",
        "message": '192.168.0.1 - - [08/Dec/2023:06:05:47 +0000] "GET" 200 - "-" "requests"',
        "method": "GET",
        "path": "/test?foo=bar",
        "pid": "<42>",
        "process_id": expected_pid,
        "referer": "-",
        "remote_ip": "192.168.0.1",
        "status": "200",
        "thread_name": "MainThread",
        "time": "2023-12-08T06:05:47+00:00",
        "timestamp": "2023-12-08 06:05:47,319",
        "user_agent": "requests",
    }


def test_gunicorn_json_capable_logger__non_existent_setting__not_raises(
    settings: SettingsWrapper,
) -> None:
    # Given
    del settings.LOG_FORMAT
    config = Config()

    # When & Then
    from util.logging import GunicornJsonCapableLogger

    GunicornJsonCapableLogger(config)
