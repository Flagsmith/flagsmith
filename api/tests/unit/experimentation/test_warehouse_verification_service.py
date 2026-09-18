import pytest
from clickhouse_connect.driver.exceptions import DatabaseError, OperationalError
from pytest_mock import MockerFixture
from urllib3 import PoolManager

from experimentation import warehouse_verification_service
from experimentation.models import WarehouseConnection


def test_delivery_client__incomplete_config__raises_config_error(
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.credentials = None

    # When / Then
    with pytest.raises(
        warehouse_verification_service.DeliveryConfigError,
        match="incomplete",
    ):
        with warehouse_verification_service.delivery_client(
            clickhouse_connection,
            send_receive_timeout=5,
        ):
            pass  # pragma: no cover


def test_delivery_client__internal_host__raises_config_error(
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.config["host"] = "10.13.37.1"  # type: ignore[index]

    # When / Then
    with pytest.raises(
        warehouse_verification_service.DeliveryConfigError,
        match="internal or private",
    ):
        with warehouse_verification_service.delivery_client(
            clickhouse_connection,
            send_receive_timeout=5,
        ):
            pass  # pragma: no cover


def test_delivery_client__valid_config__yields_http_client_and_closes(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_verification_service.clickhouse_connect.get_client",
    )

    # When
    with warehouse_verification_service.delivery_client(
        clickhouse_connection,
        send_receive_timeout=5,
    ) as client:
        # Then the stored HTTP(S) port and the caller's timeout are used as-is
        assert client is get_client.return_value
        get_client.assert_called_once_with(
            host="ch.acme-corp.example",
            port=8443,
            username="acme_svc",
            password="hunter2",
            database="acme_dwh",
            secure=True,
            connect_timeout=10,
            send_receive_timeout=5,
            pool_mgr=mocker.ANY,
        )
        # Redirects must not be followed: the internal-address guard only
        # validates the host being dialled.
        pool_manager = get_client.call_args.kwargs["pool_mgr"]
        assert isinstance(
            pool_manager,
            warehouse_verification_service._NoRedirectPoolManager,
        )
        get_client.return_value.close.assert_not_called()

    get_client.return_value.close.assert_called_once_with()


def test_delivery_client__body_raises__still_closes_client(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouse_verification_service.clickhouse_connect.get_client",
    )

    # When a query inside the block fails
    with pytest.raises(RuntimeError, match="boom"):
        with warehouse_verification_service.delivery_client(
            clickhouse_connection,
            send_receive_timeout=5,
        ):
            raise RuntimeError("boom")

    # Then the pooled HTTP connection is still released
    get_client.return_value.close.assert_called_once_with()


@pytest.mark.parametrize(
    "exists_result, expected_raise",
    [
        pytest.param([(1,)], False, id="table-exists"),
        pytest.param([(0,)], True, id="table-missing"),
    ],
)
def test_check_events_table_exists__exists_query_result__raises_only_when_missing(
    exists_result: list[tuple[int]],
    expected_raise: bool,
    mocker: MockerFixture,
) -> None:
    # Given
    client = mocker.MagicMock()
    client.query.return_value = mocker.Mock(result_rows=exists_result)

    # When / Then
    if expected_raise:
        with pytest.raises(warehouse_verification_service.MissingEventsTableError):
            warehouse_verification_service.check_events_table_exists(client)
    else:
        warehouse_verification_service.check_events_table_exists(client)
    client.query.assert_called_once_with("EXISTS TABLE events")


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        pytest.param(
            warehouse_verification_service.DeliveryConfigError(
                "Stored connection details are incomplete."
            ),
            "Stored connection details are incomplete.",
            id="config-error",
        ),
        pytest.param(
            OperationalError("HTTPSConnectionPool: Max retries exceeded"),
            "Could not connect to the host.",
            id="unreachable",
        ),
        pytest.param(
            DatabaseError("Code: 516. DB::Exception: nope", code=516),
            "Authentication failed.",
            id="bad-auth",
        ),
        pytest.param(
            DatabaseError("Code: 81. DB::Exception: no database", code=81),
            "Database does not exist.",
            id="missing-database",
        ),
        pytest.param(
            DatabaseError("Code: 60. DB::Exception: no table", code=60),
            "Events table not found in the configured database. "
            "Run the setup SQL to create it.",
            id="missing-table",
        ),
        pytest.param(
            DatabaseError("Code: 241. DB::Exception: memory limit", code=241),
            "The ClickHouse server rejected the request.",
            id="other-server-error",
        ),
        pytest.param(
            warehouse_verification_service.MissingEventsTableError(),
            "Events table not found in the configured database. "
            "Run the setup SQL to create it.",
            id="missing-events-table",
        ),
        pytest.param(
            ConnectionResetError("connection reset by peer"),
            "Connection failed.",
            id="unexpected-error",
        ),
    ],
)
def test_describe_warehouse_error__known_failures__returns_user_facing_detail(
    error: Exception,
    expected_detail: str,
) -> None:
    # Given a parametrised verification failure

    # When
    detail = warehouse_verification_service.describe_warehouse_error(error)

    # Then
    assert detail == expected_detail


def test_no_redirect_pool_manager__urlopen__refuses_to_follow_redirects(
    mocker: MockerFixture,
) -> None:
    # Given a manager asked to follow redirects, as clickhouse-connect's own
    # request path does
    urlopen = mocker.patch.object(PoolManager, "urlopen")
    manager = warehouse_verification_service._NoRedirectPoolManager()

    # When
    manager.urlopen("POST", "https://ch.acme-corp.example/", redirect=True)

    # Then the redirect is refused: a permitted host must not be able to bounce
    # the request, and its event payload, to an unchecked address
    assert urlopen.call_args.kwargs["redirect"] is False
