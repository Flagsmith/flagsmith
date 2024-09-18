from features.workflows.core.models import ChangeRequest
from features.workflows.core.tasks import delete_change_request


def test_delete_change_request(change_request: ChangeRequest) -> None:
    # Given
    assert change_request.deleted_at is None

    # When
    delete_change_request(change_request_id=change_request.id)

    # Then
    change_request.refresh_from_db()
    assert change_request.deleted_at is not None
