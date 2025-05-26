from typing import TYPE_CHECKING, Literal

from django.utils import timezone

from environments.tasks import rebuild_environment_document
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.signals import environment_feature_version_published
from features.versioning.tasks import trigger_update_version_webhooks
from features.workflows.core.exceptions import ChangeRequestNotApprovedError
from segments.models import Segment
from segments.services import SegmentCloneService
from features.models import FeatureState
from django.db.models import Q
from features.tasks import trigger_feature_state_change_webhooks
import logging


logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from features.workflows.core.models import ChangeRequest
    from users.models import FFAdminUser

FeatureStateDiff = dict[
    Literal["new_feature_state", "previous_feature_state"], FeatureState
]


class ChangeRequestCommitService:
    def __init__(self, change_request: "ChangeRequest") -> None:
        self.change_request = change_request

    def commit(self, committed_by: "FFAdminUser") -> None:
        if not self.change_request.is_approved():  # type: ignore[no-untyped-call]
            raise ChangeRequestNotApprovedError(
                "Change request has not been approved by all required approvers."
            )

        logger.debug("Committing change request #%d", self.change_request.id)

        feature_states_to_notify = self._get_feature_states_to_notify()
        self._publish_feature_states()
        self._publish_environment_feature_versions(committed_by)
        self._publish_change_sets(committed_by)
        self._publish_segments()
        for feature_state_diffs in feature_states_to_notify:
            if feature_state_diffs["previous_feature_state"]:
                trigger_feature_state_change_webhooks(
                    instance=feature_state_diffs["new_feature_state"],
                    previous_instance=feature_state_diffs[
                        "previous_feature_state"
                    ].history.first(),
                )

        self.change_request.committed_at = timezone.now()
        self.change_request.committed_by = committed_by
        self.change_request.save()

    def _get_feature_states_to_notify(
        self,
    ) -> list[FeatureStateDiff]:
        feature_states_to_notify: list[FeatureStateDiff] = []

        for feature_state in self.change_request.feature_states.all():
            latest_live_fs = self._get_previous_version_instance(feature_state)
            if latest_live_fs and latest_live_fs.version != feature_state.version:
                feature_states_to_notify.append(
                    {
                        "new_feature_state": feature_state,
                        "previous_feature_state": latest_live_fs,
                    }
                )

        return feature_states_to_notify

    def _get_previous_version_instance(
        self, feature_state: FeatureState
    ) -> FeatureState | None:
        assert feature_state.environment is not None
        fs_live_version = (
            FeatureState.objects.get_live_feature_states(
                environment=feature_state.environment,
                additional_filters=Q(
                    feature_id=feature_state.feature_id,
                    feature_segment_id=feature_state.feature_segment_id,
                    identity_id=feature_state.identity_id,
                ),
            )
            .order_by("-live_from")
            .first()
        )

        return fs_live_version

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

    def _publish_segments(self) -> None:
        for segment in self.change_request.segments.all():
            target_segment: Segment = segment.version_of  # type: ignore[assignment]
            assert target_segment != segment

            # Deep clone the segment to establish historical version this is required
            # because the target segment will be altered when the segment is published.
            # Think of it like a regular update to a segment where we create the clone
            # to create the version, then modifying the new 'draft' version with the
            # data from the change request.
            SegmentCloneService(target_segment).deep_clone()

            # Set the properties of the change request's segment to the properties
            # of the target (i.e., canonical) segment.
            target_segment.name = segment.name
            target_segment.description = segment.description
            target_segment.feature = segment.feature
            target_segment.save()

            # Delete the rules in order to replace them with copies of the segment.
            target_segment.rules.all().delete()
            for rule in segment.rules.all():
                rule.deep_clone(target_segment)
