import logging

from django.conf import settings


def get_logger(name, level=None):
    logger = logging.getLogger(name)
    logger.setLevel(level or settings.LOG_LEVEL)
    return logger