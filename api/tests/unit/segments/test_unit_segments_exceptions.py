import pytest
from rest_framework import status

from projects.models import Project
from segments.exceptions import SystemSegmentModificationError
from segments.models import Segment, SegmentManagedBy


@pytest.mark.parametrize(
    "managed_by, expected_owner",
    [
        (SegmentManagedBy.DEPENDENCY, "its flag dependency"),
        (SegmentManagedBy.EXPERIMENT, "its experiment"),
        (SegmentManagedBy.RELEASE_PIPELINE, "its release pipeline"),
        (SegmentManagedBy.UNMANAGED, "the feature that created it"),
    ],
)
def test_system_segment_modification_error__managed_segment__names_owner(
    project: Project,
    managed_by: SegmentManagedBy,
    expected_owner: str,
) -> None:
    # Given
    segment = Segment.objects.create(
        project=project,
        name="checkout-depends-on-inventory",
        is_system_segment=True,
        managed_by=managed_by,
    )

    # When
    error = SystemSegmentModificationError(segment)

    # Then
    assert error.status_code == status.HTTP_409_CONFLICT
    assert error.get_codes() == "system_segment_modification"
    assert error.detail == (
        "System segment 'checkout-depends-on-inventory' and its overrides cannot "
        f"be changed directly. Manage them through {expected_owner} instead."
    )
