import json
import logging
import sys
from datetime import datetime
from typing import Any

from django.conf import settings
from gunicorn.config import Config
from gunicorn.instrument.statsd import Statsd as GunicornLogger


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
        url = args["U"]
        if q := args["q"]:
            url += f"?{q}"

        return {
            **super().get_json_record(record),
            "time": datetime.strptime(args["t"], "[%d/%b/%Y:%H:%M:%S %z]").isoformat(),
            "path": url,
            "remote_ip": args["h"],
            "method": args["m"],
            "status": str(args["s"]),
            "user_agent": args["a"],
            "referer": args["f"],
            "duration_in_ms": args["M"],
            "pid": args["p"],
        }


class GunicornJsonCapableLogger(GunicornLogger):
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
