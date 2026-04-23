"""VCS dispatcher: entrypoints for fanning feature-external-resource
lifecycle events out to the per-provider integration side-effects
(currently only GitLab; GitHub and any future provider will land here
too — see #7315).
"""

import structlog

from features.feature_external_resources.models import (
    GITLAB_RESOURCE_TYPES,
    FeatureExternalResource,
)
from integrations.gitlab.services import (
    apply_flagsmith_label_to_resource,
    apply_initial_tag,
    deregister_gitlab_webhook_for_resource,
    register_gitlab_webhook_for_resource,
)
from integrations.gitlab.tasks import (
    post_gitlab_linked_comment,
    post_gitlab_unlinked_comment,
    remove_gitlab_label,
)

gitlab_logger = structlog.get_logger("gitlab")


def dispatch_vcs_on_resource_create(resource: FeatureExternalResource) -> None:
    """Dispatch integration side-effects after a `FeatureExternalResource`
    is created.
    """
    if resource.type in GITLAB_RESOURCE_TYPES:
        apply_flagsmith_label_to_resource(resource)
        gitlab_logger.info(
            "resource.linked",
            organisation__id=resource.feature.project.organisation_id,
            project__id=resource.feature.project_id,
            feature__id=resource.feature.id,
            resource__type=resource.type.lower(),
        )
        register_gitlab_webhook_for_resource(resource)
        apply_initial_tag(resource)
        post_gitlab_linked_comment.delay(args=(resource.id,))


def dispatch_vcs_on_resource_destroy(resource: FeatureExternalResource) -> None:
    """Dispatch integration side-effects after a `FeatureExternalResource`
    has been destroyed. `resource` is a memory-only object at this point.
    """
    if resource.type in GITLAB_RESOURCE_TYPES:
        remove_gitlab_label.delay(
            kwargs={
                "project_id": resource.feature.project_id,
                "feature_id": resource.feature_id,
                "resource_pk": resource.pk,
                "resource_url": resource.url,
                "resource_type": resource.type,
            },
        )
        post_gitlab_unlinked_comment.delay(
            args=(
                resource.feature.name,
                resource.feature.id,
                resource.url,
                resource.type,
                resource.feature.project_id,
            ),
        )
        deregister_gitlab_webhook_for_resource(resource)
        gitlab_logger.info(
            "resource.unlinked",
            organisation__id=resource.feature.project.organisation_id,
            project__id=resource.feature.project_id,
            feature__id=resource.feature.id,
            resource__type=resource.type.lower(),
        )
