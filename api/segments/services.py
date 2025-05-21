import uuid
from typing import TYPE_CHECKING
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
        self._clone_rules(to_segment=cloned)
        self._clone_metadata(to_segment=cloned)
        cloned.refresh_from_db()
        return cloned

    def shallow_clone(
        self, name: str, description: str, change_request: "ChangeRequest"
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
        clone = deepcopy(self.segment)
        clone.id = None
        clone.uuid = uuid.uuid4()
        clone.version_of = self.segment
        clone.save()

        self.segment.version += 1
        self.segment.save_without_historical_record()

        self._clone_rules(to_segment=clone)
        return clone

    def _clone_rules(self, to_segment: Segment) -> None:
        cloned_rules = []
        for rule in self.segment.rules.all():
            cloned_rules.append(rule.deep_clone(to_segment))
        to_segment.refresh_from_db()
        assert (
            self.segment.rules.count() == len(cloned_rules) == to_segment.rules.count()
        ), "Mismatch during rule cloning"

    def _clone_metadata(self, to_segment: Segment) -> None:
        cloned_metadata = []
        for metadata in self.segment.metadata.all():
            cloned_metadata.append(metadata.deep_clone_for_new_entity(to_segment))
        to_segment.refresh_from_db()
        assert (
            self.segment.metadata.count()
            == len(cloned_metadata)
            == to_segment.metadata.count()
        ), "Mismatch during metadata cloning"
