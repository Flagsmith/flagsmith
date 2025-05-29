import uuid
from copy import deepcopy
from typing import TYPE_CHECKING, Optional

from segments.models import Segment

if TYPE_CHECKING:
    from features.workflows.core.models import ChangeRequest


class SegmentCloneService:
    def __init__(self, segment: Segment):
        self.segment: Segment = segment

    def clone(self, name: str) -> Segment:
        """
        Create a standalone full clone of a Segment

        The new segment will include all rules and metadata from the original
        segment, but will have its own history.
        """
        cloned: Segment = Segment.objects.create(
            name=name,
            uuid=uuid.uuid4(),
            description=self.segment.description,
            change_request=self.segment.change_request,
            project=self.segment.project,
            feature=self.segment.feature,
            version_of=None,
        )

        self._clone_segment_rules(cloned_segment=cloned)
        self._clone_segment_metadata(cloned_segment=cloned)
        cloned.refresh_from_db()
        return cloned

    def deep_clone(self) -> Segment:
        """
        Create a versioned deep clone of the segment with rules only (no
        metadata in legacy logic), incrementing the original's version.

        TODO: Improve clarity. This method exists to allow for updating a
        segment while keeping the previous version (this) intact for history.
        We should refactor this, or at least rename it.
        """
        cloned_segment: Segment = deepcopy(self.segment)
        cloned_segment.id = None
        cloned_segment.uuid = uuid.uuid4()
        cloned_segment.version_of = self.segment
        cloned_segment.save()

        self.segment.version = (self.segment.version or 0) + 1
        self.segment.save_without_historical_record()

        self._clone_segment_rules(cloned_segment=cloned_segment)
        return cloned_segment

    # TODO: This is not used in the product, move into a test helper or refactor
    def shallow_clone(
        self,
        name: str,
        description: str,
        change_request: Optional["ChangeRequest"] = None,
    ) -> Segment:
        cloned = Segment(
            uuid=uuid.uuid4(),
            name=name,
            description=description,
            change_request=change_request,
            project=self.segment.project,
            feature=self.segment.feature,
        )

        # Keep track of the original segment
        cloned.version_of = self.segment

        cloned.history.update()
        cloned.save()
        return cloned

    def _clone_segment_rules(self, cloned_segment: Segment) -> None:
        cloned_rules = []
        for rule in self.segment.rules.all():
            cloned_rule = rule.deep_clone(cloned_segment)
            cloned_rules.append(cloned_rule)
        cloned_segment.refresh_from_db()
        assert (
            len(self.segment.rules.all())
            == len(cloned_rules)
            == len(cloned_segment.rules.all())
        ), "Mismatch during rule cloning"

    def _clone_segment_metadata(self, cloned_segment: Segment) -> None:
        cloned_metadata = []
        for metadata in self.segment.metadata.all():
            cloned_metadata.append(metadata.deep_clone_for_new_entity(cloned_segment))
        cloned_segment.refresh_from_db()
        assert (
            len(self.segment.metadata.all())
            == len(cloned_metadata)
            == len(cloned_segment.metadata.all())
        ), "Mismatch during metadata cloning"
