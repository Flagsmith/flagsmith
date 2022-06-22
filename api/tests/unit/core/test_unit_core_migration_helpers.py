from core.migration_helpers import AddDefaultUUIDs


def test_add_default_uuids_class_correctly_sets_uuid_attribute(mocker):
    # Given
    mock_apps = mocker.MagicMock()
    mock_schema_editor = mocker.MagicMock()

    mock_model_object = mocker.MagicMock()

    mock_model_class = mocker.MagicMock()
    mock_model_class.objects.all.return_value = [mock_model_object]

    mock_apps.get_model.return_value = mock_model_class

    expected_uuid = "51879740-8a55-4c46-8aeb-efddb10a01cf"
    mock_uuid = mocker.patch("core.migration_helpers.uuid")
    mock_uuid.uuid4.return_value = expected_uuid

    add_default_uuids = AddDefaultUUIDs(app_name="test", model_name="test")

    # When
    add_default_uuids(mock_apps, mock_schema_editor)

    # Then
    assert mock_model_object.uuid == expected_uuid
    mock_model_class.objects.bulk_update.assert_called_once_with(
        [mock_model_object], fields=["uuid"]
    )
