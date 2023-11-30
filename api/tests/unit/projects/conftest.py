import pytest

from segments.models import Segment


@pytest.fixture()
def segments(project):
    segments = []
    for i in range(3):
        segments.append(
            Segment.objects.create(name=f"Test Segment {i}", project=project)
        )
    return segments
