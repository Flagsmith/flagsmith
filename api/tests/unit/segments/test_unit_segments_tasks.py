from unittest.mock import Mock

from pytest_mock import MockerFixture

from segments.models import Segment
from segments.tasks import delete_segment


def test_delete_segment__existing_segment__deletes_segment(
    mocker: MockerFixture,
) -> None:
    # Given
    segment_id = 1
    segment = Mock()
    get_segment_mock = mocker.patch.object(Segment.objects, "get", return_value=segment)

    # When
    delete_segment(segment_id)

    # Then
    get_segment_mock.assert_called_once_with(pk=segment_id)
    segment.delete.assert_called_once_with()


def test_delete_segment__missing_segment__does_not_raise(
    mocker: MockerFixture,
) -> None:
    # Given
    segment_id = 1
    get_segment_mock = mocker.patch.object(
        Segment.objects, "get", side_effect=Segment.DoesNotExist
    )

    # When
    delete_segment(segment_id)

    # Then
    get_segment_mock.assert_called_once_with(pk=segment_id)
