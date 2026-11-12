from django.db import models


class SegmentFlagReference(models.Model):
    """A reference to a pre-requisite flag from the segment

    When a segment rule points to a feature as a pre-requisite, an object of
    this type must exist to materialise the relationship and enable easier
    backreferencing, e.g. for validating circular dependencies, and querying
    without inferring from JSON rules.
    """

    segment = models.ForeignKey(
        "segments.Segment",
        on_delete=models.CASCADE,
        related_name="flag_references",
    )

    prerequisite_feature = models.ForeignKey(
        "features.Feature",
        on_delete=models.CASCADE,
        related_name="segment_references",
    )

    # JSONPath (RFC 9535) locating the rule condition
    condition_json_path = models.TextField()
