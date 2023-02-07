import logging
import time
from argparse import ArgumentParser
from datetime import datetime

from django.core.management import BaseCommand
from django.db import OperationalError, connections

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser):
        parser.add_argument(
            "--waitfor",
            type=int,
            help="Number of seconds to wait for db to become available.",
            default=5,
        )

    def handle(self, *args, **options):
        wait_for = options["waitfor"]
        start = datetime.now()
        wait_between_checks = 0.25

        logger.info("Checking if database is ready for connections.")

        while True:
            if (datetime.now() - start).total_seconds() > wait_for:
                msg = f"Failed to connect to DB within {wait_for} seconds."
                logger.error(msg)
                exit(msg)

            conn = connections.create_connection("default")
            try:
                with conn.temporary_connection() as cursor:
                    cursor.execute("SELECT 1")
                logger.info("Successfully connected to the database.")
                return
            except OperationalError:
                logger.warning("Database not yet ready for connections.")

            time.sleep(wait_between_checks)
