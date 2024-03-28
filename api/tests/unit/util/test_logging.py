import json
import logging

from util.logging import JsonFormatter


def test_json_formatter():
    json_formatter = JsonFormatter()

    log_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="This is a test.",
        args=(),
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


def test_json_formatter_with_old_style_placeholders():
    json_formatter = JsonFormatter()

    log_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="example.py",
        lineno=42,
        msg="This is a test with old-style placeholders: %s and %s",
        args=("arg1", "arg2"),
        exc_info=None,
    )

    formatted_message = json_formatter.format(log_record)
    parsed_json = json.loads(formatted_message)
    assert (
        parsed_json["message"]
        == "This is a test with old-style placeholders: arg1 and arg2"
    )


def test_json_formatter_arguments_with_new_style_placeholders():
    json_formatter = JsonFormatter()
    log_record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="example.py",
        lineno=42,
        msg="This is a test with new-style placeholders: {} and {}",
        args=("arg1", "arg2"),
        exc_info=None,
    )

    formatted_message = json_formatter.format(log_record)
    parsed_json = json.loads(formatted_message)
    assert (
        parsed_json["message"]
        == "This is a test with new-style placeholders: arg1 and arg2"
    )
