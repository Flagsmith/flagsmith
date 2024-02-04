import logging
import json


class JsonFormatter(logging.Formatter):
    """Custom formatter for json logs."""
    def format(self, record):
        try:
            log_message = record.msg.replace('"', "'").replace('%s', '{}')
            formatted_message = log_message.format(*record.args)
            log_record = {
                'levelname': record.levelname,
                'message': formatted_message,
                'timestamp': self.formatTime(record, self.datefmt),
                'logger_name': record.name,
                'process_id': record.process,
                'thread_name': record.threadName,
            }
            return json.dumps(log_record)
        except Exception as e:
            return f'Error formatting log record: {str(e)}'