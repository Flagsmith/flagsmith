from django.core.management import call_command
from pytest_mock import MockerFixture


def test_dumporganisationtos3_command__calls_exporter(mocker: MockerFixture) -> None:
    # Given
    mock_exporter = mocker.MagicMock()
    mocker.patch(
        "import_export.management.commands.dumporganisationtos3.S3OrganisationExporter",
        return_value=mock_exporter,
    )

    # When
    call_command("dumporganisationtos3", "1", "test-bucket", "test-key")

    # Then
    mock_exporter.export_to_s3.assert_called_once_with(1, "test-bucket", "test-key")
