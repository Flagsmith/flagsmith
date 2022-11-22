from inspect import getmro

from django.apps import AppConfig
from simple_history.models import HistoricalChanges
from simple_history.signals import post_create_historical_record


class BaseAppConfig(AppConfig):
    def ready(self):
        from core.signals import create_audit_log_from_historical_record

        for _ in filter(lambda m: HistoricalChanges in getmro(m), self.get_models()):
            post_create_historical_record.connect(
                create_audit_log_from_historical_record
            )
