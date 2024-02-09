import json
import logging


class JsonFormatter(logging.Formatter):
    """Custom formatter for json logs."""

    def format(self, record):
        """
        %s is replaced with {} because legacy string formatting
        conventions in django-axes module prevent correct
        interpolation of arguments when using this formatter.
        """
        try:
            log_message = record.msg.replace("%s", "{}")
            formatted_message = log_message.format(*record.args)
            log_record = {
                "levelname": record.levelname,
                "message": formatted_message,
                "timestamp": self.formatTime(record, self.datefmt),
                "logger_name": record.name,
                "process_id": record.process,
                "thread_name": record.threadName,
            }
            return json.dumps(log_record)
        except (ValueError, TypeError) as e:
            return f"Error formatting log record: {str(e)}"
