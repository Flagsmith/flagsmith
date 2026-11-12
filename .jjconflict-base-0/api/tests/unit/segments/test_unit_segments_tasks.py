from projects.models import Project
from segments.models import Segment
from segments.tasks import delete_segment


def test_delete_segment__segment_exists__soft_deletes_segment(
    project: Project,
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)

    # When
    delete_segment(segment_id=segment.id)

    # Then
    segment.refresh_from_db()
    assert segment.deleted_at is not None


def test_delete_segment__segment_already_deleted__does_not_raise(
    project: Project,
) -> None:
    # Given
    segment = Segment.objects.create(name="Test Segment", project=project)
    segment_id = segment.id
    segment.hard_delete()

    # When
    delete_segment(segment_id=segment_id)  # should not raise

    # Then
    assert not Segment.objects.all_with_deleted().filter(id=segment_id).exists()
