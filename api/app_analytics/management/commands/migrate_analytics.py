import argparse
from typing import Any

from app_analytics.migrate_to_pg import migrate_feature_evaluations
from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--migrate-till",
            type=int,
            dest="migrate_till",
            help="Migrate data till n days ago",
            default=30,
        )

    def handle(self, *args: Any, migrate_till: int, **options: Any) -> None:
        migrate_feature_evaluations(migrate_till)
