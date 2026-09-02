from django.apps import apps
from django.conf import settings
from pytest_mock import MockerFixture

from clickhouse.apps import CLICKHOUSE_BACKEND_MODULE, ClickHouseConfig


def test_clickhouse_config_ready__clickhouse_configured__applies_backend_patches(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(settings.DATABASES)
    settings.DATABASES["clickhouse"] = {"ENGINE": "core.db_backends.clickhouse"}
    import_module = mocker.patch("clickhouse.apps.importlib.import_module")
    config = apps.get_app_config("clickhouse")
    assert isinstance(config, ClickHouseConfig)

    # When
    config.ready()

    # Then
    import_module.assert_called_once_with(CLICKHOUSE_BACKEND_MODULE)


def test_clickhouse_config_ready__clickhouse_not_configured__leaves_django_unpatched(
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch.dict(settings.DATABASES)
    settings.DATABASES.pop("clickhouse", None)
    import_module = mocker.patch("clickhouse.apps.importlib.import_module")
    config = apps.get_app_config("clickhouse")
    assert isinstance(config, ClickHouseConfig)

    # When
    config.ready()

    # Then
    import_module.assert_not_called()
