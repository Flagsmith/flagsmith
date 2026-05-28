from enum import Enum

from features.feature_external_resources.models import ResourceType

AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS = 10

AZURE_DEVOPS_API_VERSION = "7.1"

AZURE_DEVOPS_TAG_COLOR = "#0078D4"


class AzureDevOpsTagLabel(Enum):
    PR_OPEN = "PR Open"
    PR_MERGED = "PR Merged"
    PR_ABANDONED = "PR Abandoned"
    PR_DRAFT = "PR Draft"
    WORK_ITEM_OPEN = "Work Item Open"
    WORK_ITEM_CLOSED = "Work Item Closed"


AZURE_DEVOPS_TAG_KIND_BY_LABEL: dict[AzureDevOpsTagLabel, str] = {
    AzureDevOpsTagLabel.PR_OPEN: "PR",
    AzureDevOpsTagLabel.PR_MERGED: "PR",
    AzureDevOpsTagLabel.PR_ABANDONED: "PR",
    AzureDevOpsTagLabel.PR_DRAFT: "PR",
    AzureDevOpsTagLabel.WORK_ITEM_OPEN: "Work Item",
    AzureDevOpsTagLabel.WORK_ITEM_CLOSED: "Work Item",
}


AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE: dict[str, str] = {
    ResourceType.AZURE_DEVOPS_PULL_REQUEST.value: "PR",
    ResourceType.AZURE_DEVOPS_WORK_ITEM.value: "Work Item",
}


AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL: dict[AzureDevOpsTagLabel, str] = {
    AzureDevOpsTagLabel.PR_OPEN: "Has a linked Azure DevOps pull request open",
    AzureDevOpsTagLabel.PR_MERGED: "Has a linked Azure DevOps pull request merged",
    AzureDevOpsTagLabel.PR_ABANDONED: "Has a linked Azure DevOps pull request abandoned",
    AzureDevOpsTagLabel.PR_DRAFT: "Has a linked Azure DevOps pull request in draft",
    AzureDevOpsTagLabel.WORK_ITEM_OPEN: "Has a linked Azure DevOps work item open",
    AzureDevOpsTagLabel.WORK_ITEM_CLOSED: "Has a linked Azure DevOps work item closed",
}
