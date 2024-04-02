import json
import logging

from util.logging import JsonFormatter


def test_json_formatter__outputs_expected():
    json_formatter = JsonFormatter()

    log_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="This is a test message with args: %s and %s",
        args=("arg1", "arg2"),
        exc_info=None,
    )
    formatted_message = json_formatter.format(log_record)
    json_message = json.loads(formatted_message)

    assert "levelname" in json_message
    assert "message" in json_message
    assert "timestamp" in json_message
    assert "logger_name" in json_message
    assert "process_id" in json_message
    assert "thread_name" in json_message
    assert json_message["message"] == "This is a test message with args: arg1 and arg2"
