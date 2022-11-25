from django.apps import AppConfig
from simple_history.signals import post_create_historical_record


class BaseAppConfig(AppConfig):
    def ready(self):
        from core.signals import create_audit_log_from_historical_record

        for model_class in filter(
            lambda m: getattr(m, "include_in_audit", False), self.get_models()
        ):
            post_create_historical_record.connect(
                create_audit_log_from_historical_record, sender=model_class
            )
