from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from clickhouse_connect.driver.exceptions import DatabaseError, OperationalError
from pytest_mock import MockerFixture
from urllib3 import PoolManager

from experimentation.dataclasses import (
    ConversionBucket,
    ExposureBucket,
    MetricSpec,
    ResultsAggregates,
)
from experimentation.models import (
    MetricAggregation,
    WarehouseConnection,
)
from experimentation.stats import VariantStats
from experimentation.warehouses import clickhouse
from experimentation.warehouses.exceptions import (
    DeliveryConfigError,
    MissingEventsTableError,
)


def test_delivery_client__incomplete_config__raises_config_error(
    clickhouse_connection: WarehouseConnection,
) -> None:
    # Given
    clickhouse_connection.credentials = None

    # When / Then
    with pytest.raises(
        DeliveryConfigError,
        match="incomplete",
    ):
        with clickhouse.delivery_client(
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
        DeliveryConfigError,
        match="internal or private",
    ):
        with clickhouse.delivery_client(
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
        "experimentation.warehouses.clickhouse.clickhouse_connect.get_client",
    )

    # When
    with clickhouse.delivery_client(
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
            clickhouse._NoRedirectPoolManager,
        )
        get_client.return_value.close.assert_not_called()

    get_client.return_value.close.assert_called_once_with()


def test_delivery_client__body_raises__still_closes_client(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given
    get_client = mocker.patch(
        "experimentation.warehouses.clickhouse.clickhouse_connect.get_client",
    )

    # When a query inside the block fails
    with pytest.raises(RuntimeError, match="boom"):
        with clickhouse.delivery_client(
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
        with pytest.raises(MissingEventsTableError):
            clickhouse.check_events_table_exists(client)
    else:
        clickhouse.check_events_table_exists(client)
    client.query.assert_called_once_with("EXISTS TABLE events")


@pytest.mark.parametrize(
    "error, expected_detail",
    [
        pytest.param(
            DeliveryConfigError("Stored connection details are incomplete."),
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
            DatabaseError(
                "Code: 194. DB::Exception: default: Authentication failed: "
                "password is incorrect, or there is no user with such name",
                code=194,
            ),
            "Authentication failed.",
            id="bad-password",
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
            MissingEventsTableError(),
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
    detail = clickhouse.describe_warehouse_error(error)

    # Then
    assert detail == expected_detail


def test_no_redirect_pool_manager__urlopen__refuses_to_follow_redirects(
    mocker: MockerFixture,
) -> None:
    # Given a manager asked to follow redirects, as clickhouse-connect's own
    # request path does
    urlopen = mocker.patch.object(PoolManager, "urlopen")
    manager = clickhouse._NoRedirectPoolManager()

    # When
    manager.urlopen("POST", "https://ch.acme-corp.example/", redirect=True)

    # Then the redirect is refused: a permitted host must not be able to bounce
    # the request, and its event payload, to an unchecked address
    assert urlopen.call_args.kwargs["redirect"] is False


WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 8, tzinfo=timezone.utc)


BUCKET = datetime(2026, 1, 2, tzinfo=timezone.utc)
EXPOSURE_BUCKET_COLUMNS = (
    "quarantined",
    "variant",
    "bucket",
    "first_exposed_identities",
)


def _query_result(
    mocker: MockerFixture,
    rows: list[tuple[object, ...]],
    columns: tuple[str, ...],
) -> MagicMock:
    result: MagicMock = mocker.MagicMock(result_rows=rows, column_names=columns)
    return result


def test_clickhouse_warehouse__get_exposure_buckets__reads_customer_store(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given the customer's ClickHouse holds one exposure row per variant
    get_client = mocker.patch(
        "experimentation.warehouses.clickhouse.clickhouse_connect.get_client",
    )
    client = get_client.return_value
    client.query.return_value = _query_result(
        mocker,
        [(0, "control", BUCKET, 10), (1, "", BUCKET, 2)],
        EXPOSURE_BUCKET_COLUMNS,
    )

    # When
    buckets = clickhouse.ClickHouseWarehouse().get_exposure_buckets(
        clickhouse_connection,
        environment_key="key",
        feature_name="checkout",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        granularity="day",
    )

    # Then the rows are mapped to buckets
    assert buckets == [
        ExposureBucket("control", BUCKET, first_exposed_identities=10),
        ExposureBucket("", BUCKET, first_exposed_identities=2, quarantined=True),
    ]
    # And the read uses the background timeout and pinned settings
    assert (
        get_client.call_args.kwargs["send_receive_timeout"]
        == clickhouse.BACKGROUND_QUERY_TIMEOUT_SECONDS
    )
    (query,) = client.query.call_args.args
    assert "toStartOfDay(first_exposure, 'UTC') AS bucket" in query
    assert client.query.call_args.kwargs == {
        "parameters": {
            "environment_key": "key",
            "exposure_event": "$flag_exposure",
            "feature_name": "checkout",
            "window_start": WINDOW_START,
            "window_end": WINDOW_END,
        },
        "settings": clickhouse.RESULTS_QUERY_SETTINGS,
    }
    client.close.assert_called_once_with()


def test_clickhouse_warehouse__get_results_aggregates__reads_customer_store(
    clickhouse_connection: WarehouseConnection,
    mocker: MockerFixture,
) -> None:
    # Given the customer's ClickHouse answers the results, conversions and
    # exposure buckets queries in turn
    get_client = mocker.patch(
        "experimentation.warehouses.clickhouse.clickhouse_connect.get_client",
    )
    client = get_client.return_value
    client.query.side_effect = [
        _query_result(
            mocker,
            [("control", 100, 12.0, 12.0)],
            ("variant", "n", "m0_sum", "m0_sum_squares"),
        ),
        _query_result(
            mocker,
            [("control", 0, BUCKET, 12)],
            ("variant", "metric_index", "bucket", "converted_identities"),
        ),
        _query_result(mocker, [(0, "control", BUCKET, 100)], EXPOSURE_BUCKET_COLUMNS),
    ]
    spec = MetricSpec(
        metric_id=7,
        event="purchase",
        aggregation=MetricAggregation.OCCURRENCE,
        lower_is_better=False,
    )

    # When
    aggregates = clickhouse.ClickHouseWarehouse().get_results_aggregates(
        clickhouse_connection,
        environment_key="key",
        feature_name="checkout",
        window_start=WINDOW_START,
        window_end=WINDOW_END,
        specs=[spec],
        granularity="hour",
    )

    # Then the statistics and chart rows come from the customer's store
    assert aggregates == ResultsAggregates(
        specs=[spec],
        exposure_counts={"control": 100},
        metric_stats={7: {"control": VariantStats(n=100, sum=12.0, sum_squares=12.0)}},
        granularity="hour",
        exposure_buckets=[
            ExposureBucket("control", BUCKET, first_exposed_identities=100)
        ],
        conversion_buckets={7: [ConversionBucket("control", BUCKET, 12)]},
    )
    # And all three reads share one client with the pinned settings
    get_client.assert_called_once()
    assert all(
        call.kwargs["settings"] == clickhouse.RESULTS_QUERY_SETTINGS
        for call in client.query.call_args_list
    )
    client.close.assert_called_once_with()
