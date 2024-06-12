from app_analytics.constants import ANALYTICS_READ_BUCKET_SIZE
from app_analytics.influxdb_wrapper import influxdb_client, read_bucket
from app_analytics.models import FeatureEvaluationBucket


def migrate_feature_evaluations(migrate_till: int = 30) -> None:
    query_api = influxdb_client.query_api()

    for i in range(migrate_till):
        range_start = f"-{i+1}d"
        range_stop = f"-{i}d"
        query = (
            f'from (bucket: "{read_bucket}") '
            f"|> range(start: {range_start}, stop: {range_stop}) "
            f'|> filter(fn: (r) => r._measurement == "feature_evaluation")'
        )

        result = query_api.query(query)

        feature_evaluations = []
        for table in result:
            for record in table.records:
                feature_evaluations.append(
                    FeatureEvaluationBucket(
                        feature_name=record.values["feature_id"],
                        bucket_size=ANALYTICS_READ_BUCKET_SIZE,
                        created_at=record.get_time(),
                        total_count=record.get_value(),
                        environment_id=record.values["environment_id"],
                    )
                )
        FeatureEvaluationBucket.objects.bulk_create(feature_evaluations)
