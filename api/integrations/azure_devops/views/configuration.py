import structlog
from structlog.typing import FilteringBoundLogger

from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    AzureDevOpsConfigurationSerializer,
)
from integrations.common.views import ProjectIntegrationBaseViewSet

logger = structlog.get_logger("azure_devops")


class AzureDevOpsConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = AzureDevOpsConfigurationSerializer  # type: ignore[assignment]
    model_class = AzureDevOpsConfiguration  # type: ignore[assignment]
    pagination_class = None

    def _log_for(self, config: AzureDevOpsConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            organisation__id=config.project.organisation_id,
            project__id=config.project.id,
        )

    def perform_create(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        super().perform_create(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.created",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_update(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        super().perform_update(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.updated",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_destroy(self, instance: AzureDevOpsConfiguration) -> None:
        log = self._log_for(instance)
        super().perform_destroy(instance)
        log.info("configuration.deleted")
