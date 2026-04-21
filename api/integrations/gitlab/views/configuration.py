import structlog
from structlog.typing import FilteringBoundLogger

from integrations.common.views import ProjectIntegrationBaseViewSet
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.serializers import GitLabConfigurationSerializer
from integrations.gitlab.tasks import (
    deregister_gitlab_webhooks,
    register_gitlab_webhooks,
)

logger = structlog.get_logger("gitlab")


class GitLabConfigurationViewSet(ProjectIntegrationBaseViewSet):
    serializer_class = GitLabConfigurationSerializer  # type: ignore[assignment]
    model_class = GitLabConfiguration  # type: ignore[assignment]
    pagination_class = None

    def _log_for(self, config: GitLabConfiguration) -> FilteringBoundLogger:
        return logger.bind(  # type: ignore[no-any-return]
            project__id=config.project.id,
            organisation__id=config.project.organisation_id,
        )

    def perform_create(self, serializer: GitLabConfigurationSerializer) -> None:  # type: ignore[override]
        super().perform_create(serializer)
        instance: GitLabConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.created",
            gitlab_instance_url=instance.gitlab_instance_url,
        )
        register_gitlab_webhooks.delay(args=(instance.id,))

    def perform_update(self, serializer: GitLabConfigurationSerializer) -> None:  # type: ignore[override]
        super().perform_update(serializer)
        instance: GitLabConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.updated",
            gitlab_instance_url=instance.gitlab_instance_url,
        )
        register_gitlab_webhooks.delay(args=(instance.id,))

    def perform_destroy(self, instance: GitLabConfiguration) -> None:
        log = self._log_for(instance)
        super().perform_destroy(instance)
        log.info("configuration.deleted")
        deregister_gitlab_webhooks.delay(args=(instance.id,))
