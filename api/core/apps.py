from django.apps import AppConfig
from simple_history.signals import (
    post_create_historical_record,
    pre_create_historical_record,
)


class BaseAppConfig(AppConfig):
    """
    A Base AppConfig class that all apps should inherit from

    It ensures that the correct signals are attached for handling the writing of AuditLog records
    based on the creation of HistoricalRecords (as per functionality in django-simple-history).
    """

    name = "core"

    def ready(self):
        from core.signals import (
            add_master_api_key,
            create_audit_log_from_historical_record,
        )

        for model_class in filter(
            lambda m: getattr(m, "include_in_audit", False), self.get_models()
        ):
            post_create_historical_record.connect(
                create_audit_log_from_historical_record, sender=model_class
            )
            pre_create_historical_record.connect(add_master_api_key, sender=model_class)
