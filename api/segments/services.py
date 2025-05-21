import uuid
from typing import TYPE_CHECKING, Optional
from copy import deepcopy

from segments.models import Segment

if TYPE_CHECKING:
    from features.workflows.core.models import ChangeRequest


class SegmentCloner:
    def __init__(self, segment: Segment):
        self.segment = segment

    def clone(self, name: str) -> Segment:
        cloned = Segment.objects.create(
            name=name,
            uuid=uuid.uuid4(),
            description=self.segment.description,
            change_request=self.segment.change_request,
            project=self.segment.project,
            feature=self.segment.feature,
            version_of=None,
        )
        self.clone_segment_rules(cloned_segment=cloned)
        self._clone_segment_metadata(cloned_segment=cloned)
        cloned.refresh_from_db()
        return cloned

    def shallow_clone(
        self,
        name: str,
        description: str,
        change_request: Optional["ChangeRequest"] = None,
    ) -> Segment:
        cloned_segment = Segment(
            version_of=self.segment,
            uuid=uuid.uuid4(),
            name=name,
            description=description,
            change_request=change_request,
            project=self.segment.project,
            feature=self.segment.feature,
            version=None,
        )
        cloned_segment.history.update()
        cloned_segment.save()
        return cloned_segment

    def deep_clone(self) -> Segment:
        """
        Create a versioned deep clone of the segment with rules only (no metadata in legacy logic),
        incrementing the original's version.
        """
        cloned_segment = deepcopy(self.segment)
        cloned_segment.id = None
        cloned_segment.uuid = uuid.uuid4()
        cloned_segment.version_of = self.segment
        cloned_segment.save()

        self.segment.version = self.segment.version + 1
        self.segment.save_without_historical_record()

        self.clone_segment_rules(cloned_segment=cloned_segment)
        return cloned_segment

    def clone_segment_rules(self, cloned_segment: Segment) -> None:
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
