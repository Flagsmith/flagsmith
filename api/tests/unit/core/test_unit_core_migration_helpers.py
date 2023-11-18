from core.migration_helpers import AddDefaultUUIDs, PostgresOnlyRunSQL


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


def test_postgres_only_run_sql__from_sql_file__with_reverse_sql_as_string(
    mocker, tmp_path
):
    # Given
    forward_sql = "SELECT 1;"
    reverse_sql = "SELECT 2;"

    # Create a temporary file
    sql_file = tmp_path / "forward_test.sql"
    sql_file.write_text(forward_sql)

    mocked_init = mocker.patch(
        "core.migration_helpers.PostgresOnlyRunSQL.__init__", return_value=None
    )

    # When
    PostgresOnlyRunSQL.from_sql_file(sql_file, reverse_sql)

    # Then
    mocked_init.assert_called_once_with(forward_sql, reverse_sql=reverse_sql)


def test_postgres_only_run_sql__from_sql_file__with_reverse_sql_as_file_path(
    mocker, tmp_path
):
    # Given
    forward_sql = "SELECT 1;"
    reverse_sql = "SELECT 2;"

    # Create  temporary files
    forward_sql_file = tmp_path / "forward_test.sql"
    forward_sql_file.write_text(forward_sql)

    reverse_sql_file = tmp_path / "reverse_test.sql"
    reverse_sql_file.write_text(reverse_sql)

    mocked_init = mocker.patch(
        "core.migration_helpers.PostgresOnlyRunSQL.__init__", return_value=None
    )

    # When
    PostgresOnlyRunSQL.from_sql_file(forward_sql_file, reverse_sql_file)

    # Then
    mocked_init.assert_called_once_with(forward_sql, reverse_sql=reverse_sql)


def test_postgres_only_run_sql__from_sql_file__without_reverse_sql(mocker, tmp_path):
    # Given
    forward_sql = "SELECT 1;"

    # Create  temporary files
    forward_sql_file = tmp_path / "forward_test.sql"
    forward_sql_file.write_text(forward_sql)

    mocked_init = mocker.patch(
        "core.migration_helpers.PostgresOnlyRunSQL.__init__", return_value=None
    )

    # When
    PostgresOnlyRunSQL.from_sql_file(forward_sql_file)

    # Then
    mocked_init.assert_called_once_with(forward_sql, reverse_sql=None)
