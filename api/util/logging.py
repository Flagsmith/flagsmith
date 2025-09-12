import json
import logging
import sys
from datetime import datetime
from typing import Any

from django.conf import settings
from gunicorn.config import Config  # type: ignore[import-untyped]
from gunicorn.instrument.statsd import (  # type: ignore[import-untyped]
    Statsd as GunicornLogger,
)


class JsonFormatter(logging.Formatter):
    """Custom formatter for json logs."""

    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        formatted_message = record.getMessage()
        json_record = {
            "levelname": record.levelname,
            "message": formatted_message,
            "timestamp": self.formatTime(record, self.datefmt),
            "logger_name": record.name,
            "process_id": record.process,
            "thread_name": record.threadName,
        }
        if record.exc_info:
            json_record["exc_info"] = self.formatException(record.exc_info)
        return json_record

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(self.get_json_record(record))


class GunicornAccessLogJsonFormatter(JsonFormatter):
    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        args = record.args
        url = args["U"]  # type: ignore[call-overload,index]
        if q := args["q"]:  # type: ignore[call-overload,index]
            url += f"?{q}"  # type: ignore[operator]

        return {
            **super().get_json_record(record),
            "time": datetime.strptime(args["t"], "[%d/%b/%Y:%H:%M:%S %z]").isoformat(),  # type: ignore[arg-type,call-overload,index]  # noqa: E501  # noqa: E501
            "path": url,
            "remote_ip": args["h"],  # type: ignore[call-overload,index]
            "method": args["m"],  # type: ignore[call-overload,index]
            "status": str(args["s"]),  # type: ignore[call-overload,index]
            "user_agent": args["a"],  # type: ignore[call-overload,index]
            "referer": args["f"],  # type: ignore[call-overload,index]
            "duration_in_ms": args["M"],  # type: ignore[call-overload,index]
            "pid": args["p"],  # type: ignore[call-overload,index]
        }


class GunicornJsonCapableLogger(GunicornLogger):  # type: ignore[misc]
    def setup(self, cfg: Config) -> None:
        super().setup(cfg)
        if getattr(settings, "LOG_FORMAT", None) == "json":
            self._set_handler(
                self.error_log,
                cfg.errorlog,
                JsonFormatter(),
            )
            self._set_handler(
                self.access_log,
                cfg.accesslog,
                GunicornAccessLogJsonFormatter(),
                stream=sys.stdout,
            )
