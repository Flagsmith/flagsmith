from users.tasks import create_pipedrive_lead


def test_create_pipedrive_lead(mocker, admin_user):
    # Given
    mock_lead_tracker = mocker.MagicMock()
    mocker.patch("users.tasks.PipedriveLeadTracker", return_value=mock_lead_tracker)

    # When
    create_pipedrive_lead(admin_user.id)

    # Then
    mock_lead_tracker.create_lead.assert_called_once_with(admin_user)
