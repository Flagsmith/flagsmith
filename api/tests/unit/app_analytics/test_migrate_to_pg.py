import pytest
from app_analytics.migrate_to_pg import migrate_feature_evaluations
from app_analytics.models import FeatureEvaluationBucket
from django.conf import settings
from django.utils import timezone
from pytest_mock import MockerFixture


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is not configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_migrate_feature_evaluations(mocker: MockerFixture) -> None:
    # Given
    feature_name = "test_feature_one"
    environment_id = "1"

    # mock the read bucket name
    read_bucket = "test_bucket"
    mocker.patch("app_analytics.migrate_to_pg.read_bucket", read_bucket)

    # Next, mock the influx client and create some records
    mock_influxdb_client = mocker.patch("app_analytics.migrate_to_pg.influxdb_client")
    mock_query_api = mock_influxdb_client.query_api.return_value
    mock_tables = []
    for i in range(3):
        mock_record = mocker.MagicMock(
            values={"feature_id": feature_name, "environment_id": environment_id},
            spec_set=["values", "get_time", "get_value"],
        )
        mock_record.get_time.return_value = timezone.now() - timezone.timedelta(days=i)  # type: ignore[attr-defined]
        mock_record.get_value.return_value = 100

        mock_table = mocker.MagicMock(records=[mock_record], spec_set=["records"])
        mock_tables.append(mock_table)

    mock_query_api.query.side_effect = [[table] for table in mock_tables]

    # When
    migrate_feature_evaluations(migrate_till=3)

    # Then - only 3 records should be created
    assert FeatureEvaluationBucket.objects.count() == 3
    assert (
        FeatureEvaluationBucket.objects.filter(
            feature_name=feature_name,
            environment_id=environment_id,
            bucket_size=15,
            total_count=100,
        ).count()
        == 3
    )
    # And, the query should have been called 3 times
    mock_query_api.assert_has_calls(
        [
            mocker.call.query(
                (
                    f'from (bucket: "{read_bucket}") '
                    f"|> range(start: -1d, stop: -0d) "
                    f'|> filter(fn: (r) => r._measurement == "feature_evaluation")'
                )
            ),
            mocker.call.query(
                (
                    f'from (bucket: "{read_bucket}") '
                    f"|> range(start: -2d, stop: -1d) "
                    f'|> filter(fn: (r) => r._measurement == "feature_evaluation")'
                )
            ),
            mocker.call.query(
                (
                    f'from (bucket: "{read_bucket}") '
                    f"|> range(start: -3d, stop: -2d) "
                    f'|> filter(fn: (r) => r._measurement == "feature_evaluation")'
                )
            ),
        ]
    )
