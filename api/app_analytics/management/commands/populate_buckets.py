import argparse
from typing import Any

from app_analytics.constants import ANALYTICS_READ_BUCKET_SIZE
from app_analytics.tasks import (
    populate_api_usage_bucket,
    populate_feature_evaluation_bucket,
)
from django.conf import settings
from django.core.management import BaseCommand

MINUTES_IN_DAY: int = 1440


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--days-to-populate",
            type=int,
            dest="days_to_populate",
            help="Last n days to populate",
            default=30,
        )

    def handle(self, *args: Any, days_to_populate: int, **options: Any) -> None:
        if settings.USE_POSTGRES_FOR_ANALYTICS:
            minutes_to_populate = MINUTES_IN_DAY * days_to_populate
            populate_api_usage_bucket(
                ANALYTICS_READ_BUCKET_SIZE,
                minutes_to_populate,
            )
            populate_feature_evaluation_bucket(
                ANALYTICS_READ_BUCKET_SIZE,
                minutes_to_populate,
            )
