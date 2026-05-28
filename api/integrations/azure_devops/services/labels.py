import requests
import structlog

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from integrations.azure_devops.client import (
    add_tag_to_pull_request,
    add_tag_to_work_item,
    remove_tag_from_pull_request,
    remove_tag_from_work_item,
)
from integrations.azure_devops.constants import AZURE_DEVOPS_FLAGSMITH_LABEL
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.url_parsing import (
    parse_pull_request_url,
    parse_work_item_url,
)

logger = structlog.get_logger("azure_devops")


def _config_for_project(project_id: int) -> AzureDevOpsConfiguration | None:
    """Load the AzureDevOpsConfiguration with labeling_enabled set, or
    return None.
    """
    config: AzureDevOpsConfiguration | None = AzureDevOpsConfiguration.objects.filter(
        project_id=project_id
    ).first()
    if not config or not config.labeling_enabled:
        return None
    return config


def apply_flagsmith_label_to_resource(
    resource: FeatureExternalResource,
) -> None:
    """Apply the "flagsmith" label/tag to the linked ADO resource. No-op
    if labelling is disabled or unconfigured. Never raises — failures are
    logged via ``label.apply_failed``.
    """
    config = _config_for_project(resource.feature.project_id)
    if config is None:
        return

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
        feature__id=resource.feature_id,
        resource__type=resource.type,
    )

    try:
        if resource.type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
            ref = parse_pull_request_url(resource.url)
            if ref is None:
                return
            add_tag_to_pull_request(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=ref.project,
                pull_request_id=ref.pull_request_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.applied", ado__resource__id=ref.pull_request_id)
            return

        if resource.type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
            work_ref = parse_work_item_url(resource.url)
            if work_ref is None:
                return
            add_tag_to_work_item(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=work_ref.project,
                work_item_id=work_ref.work_item_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.applied", ado__resource__id=work_ref.work_item_id)
    except requests.RequestException:
        log.exception("label.apply_failed")


def remove_flagsmith_label_from_resource(
    *,
    project_id: int,
    resource_url: str,
    resource_type: str,
) -> None:
    """Remove the "flagsmith" label/tag from the ADO resource. Takes fields
    directly because this is called from the unlink task after the FER row
    is gone. No-op if labelling is disabled or unconfigured. Never raises.
    """
    config = _config_for_project(project_id)
    if config is None:
        return

    log = logger.bind(
        organisation__id=config.project.organisation_id,
        project__id=config.project_id,
        resource__type=resource_type,
    )

    try:
        if resource_type == ResourceType.AZURE_DEVOPS_PULL_REQUEST.value:
            ref = parse_pull_request_url(resource_url)
            if ref is None:
                return
            remove_tag_from_pull_request(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=ref.project,
                pull_request_id=ref.pull_request_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.removed", ado__resource__id=ref.pull_request_id)
            return

        if resource_type == ResourceType.AZURE_DEVOPS_WORK_ITEM.value:
            work_ref = parse_work_item_url(resource_url)
            if work_ref is None:
                return
            remove_tag_from_work_item(
                organisation_url=config.organisation_url,
                pat=config.personal_access_token,
                project=work_ref.project,
                work_item_id=work_ref.work_item_id,
                tag=AZURE_DEVOPS_FLAGSMITH_LABEL,
            )
            log.info("label.removed", ado__resource__id=work_ref.work_item_id)
    except requests.RequestException:
        log.exception("label.removal_failed")
