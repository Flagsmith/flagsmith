import requests
import structlog
from rest_framework.exceptions import ValidationError
from structlog.typing import FilteringBoundLogger

from integrations.azure_devops.client import list_projects
from integrations.azure_devops.client.exceptions import AzureDevOpsAuthError
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.serializers import (
    WRITE_ONLY_PLACEHOLDER,
    AzureDevOpsConfigurationSerializer,
)
from integrations.common.views import ProjectIntegrationBaseViewSet

logger = structlog.get_logger("azure_devops")


def _validate_pat_against_ado(*, organisation_url: str, pat: str) -> None:
    """Probe ADO with a minimal request to confirm the PAT is valid.

    Raises ``ValidationError`` on 401/403 (bad credentials) and on any
    other failure mode (5xx, network, malformed response). Surfacing a
    user-facing 400 on transient failure is better than a 500 because the
    user can act on the message; the persistence path should not silently
    accept an unverified PAT either.
    """
    try:
        list_projects(organisation_url=organisation_url, pat=pat, top=1)
    except AzureDevOpsAuthError:
        raise ValidationError(
            "Azure DevOps rejected the credentials. "
            "Check the organisation URL and personal access token."
        ) from None
    except requests.RequestException:
        raise ValidationError(
            "Azure DevOps could not be reached to validate the credentials. "
            "Please try again."
        ) from None


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
        # Surface the "already exists" error before making an external call.
        if self.get_queryset().exists():
            raise ValidationError("This integration already exists for this project.")
        _validate_pat_against_ado(
            organisation_url=serializer.validated_data["organisation_url"],
            pat=serializer.validated_data["personal_access_token"],
        )
        super().perform_create(serializer)
        instance: AzureDevOpsConfiguration = serializer.instance  # type: ignore[assignment]
        self._log_for(instance).info(
            "configuration.created",
            ado__organisation__url=instance.organisation_url,
        )

    def perform_update(self, serializer: AzureDevOpsConfigurationSerializer) -> None:  # type: ignore[override]
        pat = serializer.validated_data.get("personal_access_token")
        # Treat the masked placeholder as "no change" — the serializer drops
        # it during ``update`` so it never reaches the database, and there is
        # nothing meaningful to validate against ADO either.
        if pat is not None and pat != WRITE_ONLY_PLACEHOLDER:
            _validate_pat_against_ado(
                organisation_url=serializer.validated_data.get(
                    "organisation_url",
                    serializer.instance.organisation_url,  # type: ignore[union-attr]
                ),
                pat=pat,
            )
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
