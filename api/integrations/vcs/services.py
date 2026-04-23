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
from integrations.gitlab.services import register_gitlab_webhook_for_resource
from integrations.gitlab.tasks import (
    post_gitlab_linked_comment,
    post_gitlab_unlinked_comment,
)

gitlab_logger = structlog.get_logger("gitlab")


def dispatch_vcs_on_resource_create(resource: FeatureExternalResource) -> None:
    """Dispatch integration side-effects after a ``FeatureExternalResource``
    is created.
    """
    if resource.type in GITLAB_RESOURCE_TYPES:
        gitlab_logger.info(
            "resource.linked",
            organisation__id=resource.feature.project.organisation_id,
            project__id=resource.feature.project_id,
            feature__id=resource.feature.id,
            resource__type=resource.type.lower(),
        )
        register_gitlab_webhook_for_resource(resource)
        post_gitlab_linked_comment.delay(args=(resource.id,))


def dispatch_vcs_on_resource_destroy(resource: FeatureExternalResource) -> None:
    """Dispatch integration side-effects before a ``FeatureExternalResource``
    is destroyed.
    """
    if resource.type in GITLAB_RESOURCE_TYPES:
        post_gitlab_unlinked_comment.delay(
            args=(
                resource.feature.name,
                resource.feature.id,
                resource.url,
                resource.type,
                resource.feature.project_id,
            ),
        )
        gitlab_logger.info(
            "resource.unlinked",
            organisation__id=resource.feature.project.organisation_id,
            project__id=resource.feature.project_id,
            feature__id=resource.feature.id,
            resource__type=resource.type.lower(),
        )
