from typing import TYPE_CHECKING

import structlog
from django.db import transaction
from django.utils import timezone

from environments.tasks import rebuild_environment_document
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.signals import environment_feature_version_published
from features.versioning.tasks import trigger_update_version_webhooks
from features.workflows.core.exceptions import ChangeRequestNotApprovedError

if TYPE_CHECKING:
    from features.workflows.core.models import ChangeRequest
    from users.models import FFAdminUser

logger = structlog.get_logger()


class ChangeRequestCommitService:
    def __init__(self, change_request: "ChangeRequest") -> None:
        self.change_request = change_request

    def commit(self, committed_by: "FFAdminUser") -> None:
        if not self.change_request.is_approved():
            raise ChangeRequestNotApprovedError(
                "Change request has not been approved by all required approvers."
            )

        self._publish_feature_states()
        self._publish_environment_feature_versions(committed_by)
        self._publish_change_sets(committed_by)
        self._publish_segments()

        self.change_request.committed_at = timezone.now()
        self.change_request.committed_by = committed_by
        self.change_request.save()

    def _publish_feature_states(self) -> None:
        now = timezone.now()

        feature_states = list(self.change_request.feature_states.all())
        for fs in feature_states:
            if not fs.live_from or fs.live_from < now:
                fs.live_from = now

            fs.version = fs.get_next_version_number(
                environment_id=fs.environment_id,  # type: ignore[arg-type]
                feature_id=fs.feature_id,
                feature_segment_id=fs.feature_segment_id,  # type: ignore[arg-type]
                identity_id=fs.identity_id,  # type: ignore[arg-type]
            )

        if feature_states:
            type(fs).objects.bulk_update(feature_states, ["live_from", "version"])

    def _publish_environment_feature_versions(
        self, published_by: "FFAdminUser"
    ) -> None:
        now = timezone.now()

        if environment_feature_versions := list(
            self.change_request.environment_feature_versions.all()
        ):
            for environment_feature_version in environment_feature_versions:
                if (
                    not environment_feature_version.live_from
                    or environment_feature_version.live_from < now
                ):
                    environment_feature_version.live_from = now

                environment_feature_version.publish(published_by, persist=False)

            EnvironmentFeatureVersion.objects.bulk_update(
                environment_feature_versions,
                fields=["published_at", "published_by", "live_from"],
            )

            for environment_feature_version in environment_feature_versions:
                trigger_update_version_webhooks.delay(
                    kwargs={
                        "environment_feature_version_uuid": str(
                            environment_feature_version.uuid
                        )
                    },
                    delay_until=environment_feature_version.live_from,
                )
                rebuild_environment_document.delay(
                    kwargs={"environment_id": self.change_request.environment_id},
                    delay_until=environment_feature_version.live_from,
                )
                environment_feature_version_published.send(
                    EnvironmentFeatureVersion, instance=environment_feature_version
                )

    def _publish_change_sets(self, published_by: "FFAdminUser") -> None:
        for change_set in self.change_request.change_sets.all():
            change_set.publish(user=published_by)

    @transaction.atomic
    def _publish_segments(self) -> None:
        for draft_segment in self.change_request.segments.all():
            live_segment = draft_segment.version_of
            if not live_segment:  # pragma: no cover
                logger.warning("missing-live-segment", draft_segment=draft_segment.uuid)
                continue

            # Make a revision of the live segment
            revision = live_segment.clone(is_revision=True)
            logger.info(
                "segment-revision-created",
                segment_id=live_segment.id,
                revision_id=revision.id,
            )

            live_segment.name = draft_segment.name
            live_segment.description = draft_segment.description
            live_segment.feature = draft_segment.feature
            live_segment.save()
            live_segment.copy_rules_and_conditions_from(draft_segment)
