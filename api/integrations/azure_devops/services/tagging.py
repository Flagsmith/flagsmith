from features.feature_external_resources.models import (
    FeatureExternalResource,
)
from features.models import Feature
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_TAG_COLOR,
    AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_LABEL,
    AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE,
    AzureDevOpsTagLabel,
)
from integrations.azure_devops.mappers import map_resource_to_tag_label
from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.tags.models import Tag, TagType


def _tagging_enabled_for_resource(resource: FeatureExternalResource) -> bool:
    """True if the resource's project has an AzureDevOpsConfiguration with
    tagging_enabled set. False if there's no configuration or the toggle
    is off.
    """
    config = AzureDevOpsConfiguration.objects.filter(
        project=resource.feature.project,
    ).first()
    return bool(config and config.tagging_enabled)


def set_azure_devops_tag(feature: Feature, new_label: AzureDevOpsTagLabel) -> None:
    """Apply an Azure DevOps system tag to ``feature``, replacing any
    existing Azure DevOps tag of the same kind (PR / Work Item) first.
    """
    kind = AZURE_DEVOPS_TAG_KIND_BY_LABEL[new_label]
    feature.tags.remove(
        *feature.tags.filter(
            type=TagType.AZURE_DEVOPS.value,
            label__startswith=kind,
        )
    )
    tag, _ = Tag.objects.get_or_create(
        label=new_label.value,
        project=feature.project,
        is_system_tag=True,
        type=TagType.AZURE_DEVOPS.value,
        defaults={
            "color": AZURE_DEVOPS_TAG_COLOR,
            "description": AZURE_DEVOPS_TAG_DESCRIPTION_BY_LABEL[new_label],
        },
    )
    feature.tags.add(tag)


def apply_initial_tag(resource: FeatureExternalResource) -> None:
    """Tag ``resource.feature`` based on the linked ADO resource's state
    at link time. No-op when the project has no AzureDevOpsConfiguration,
    when tagging_enabled is False, or when the metadata can't be mapped
    to a known label.
    """
    if not _tagging_enabled_for_resource(resource):
        return
    label = map_resource_to_tag_label(resource)
    if label is None:
        return
    set_azure_devops_tag(resource.feature, label)


def clear_tag_for_resource(resource: FeatureExternalResource) -> None:
    """Remove the Azure DevOps tag for ``resource``'s kind (PR / Work Item)
    from its feature when no other linked FeatureExternalResource of the
    same kind remains. Safe to call whether ``resource`` is still in the
    DB or has already been deleted.
    """
    kind = AZURE_DEVOPS_TAG_KIND_BY_RESOURCE_TYPE.get(resource.type)
    if kind is None:
        return
    if (
        FeatureExternalResource.objects.filter(
            feature=resource.feature,
            type=resource.type,
        )
        .exclude(pk=resource.pk)
        .exists()
    ):
        return
    resource.feature.tags.remove(
        *resource.feature.tags.filter(
            type=TagType.AZURE_DEVOPS.value,
            label__startswith=kind,
        )
    )


def refresh_tags_for_resource(resource: FeatureExternalResource) -> None:
    """Re-apply the right tag for ``resource``'s current metadata. Called
    by the inbound-webhook handler (later PR) after it updates the
    metadata in place. No-op when tagging is disabled or when the state
    can't be mapped to a known label.
    """
    if not _tagging_enabled_for_resource(resource):
        return
    label = map_resource_to_tag_label(resource)
    if label is None:
        return
    set_azure_devops_tag(resource.feature, label)
