import json
import logging
import sys
from datetime import datetime
from typing import Any

from django.conf import settings
from gunicorn.config import Config
from gunicorn.glogging import Logger as GunicornLogger


class JsonFormatter(logging.Formatter):
    """Custom formatter for json logs."""

    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        formatted_message = record.getMessage()
        return {
            "levelname": record.levelname,
            "message": formatted_message,
            "timestamp": self.formatTime(record, self.datefmt),
            "logger_name": record.name,
            "process_id": record.process,
            "thread_name": record.threadName,
        }

    def format(self, record: logging.LogRecord) -> str:
        try:
            return json.dumps(self.get_json_record(record))
        except (ValueError, TypeError) as e:
            return json.dumps({"message": f"{e} when dumping log"})


class GunicornAccessLogJsonFormatter(JsonFormatter):
    def get_json_record(self, record: logging.LogRecord) -> dict[str, Any]:
        response_time = datetime.strptime(record.args["t"], "[%d/%b/%Y:%H:%M:%S %z]")
        url = record.args["U"]
        if record.args["q"]:
            url += f"?{record.args['q']}"

        return {
            **super().get_json_record(record),
            "time": response_time.isoformat(),
            "path": url,
            "remote_ip": record.args["h"],
            "method": record.args["m"],
            "status": str(record.args["s"]),
            "user_agent": record.args["a"],
            "referer": record.args["f"],
            "duration_in_ms": record.args["M"],
            "pid": record.args["p"],
        }


class GunicornJsonCapableLogger(GunicornLogger):
    def setup(self, cfg: Config) -> None:
        super().setup(cfg)
        if settings.LOG_FORMAT == "json":
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
