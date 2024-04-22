import logging
import time
from argparse import ArgumentParser
from typing import Any

from django.core.management import BaseCommand
from django.db import OperationalError, connections
from django.db.migrations.executor import MigrationExecutor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--waitfor",
            type=int,
            dest="wait_for",
            help="Number of seconds to wait for db to become available.",
            default=5,
        )
        parser.add_argument(
            "--migrations",
            action="store_true",
            dest="should_wait_for_migrations",
            help="Whether to wait until all migrations are applied.",
            default=False,
        )
        parser.add_argument(
            "--database",
            type=str,
            dest="database",
            help=(
                'The database to wait for ("default", "analytics").'
                'Defaults to the "default" database.'
            ),
            default="default",
        )

    def handle(
        self,
        *args: Any,
        wait_for: int,
        should_wait_for_migrations: bool,
        database: str,
        **options: Any,
    ) -> None:
        start = time.monotonic()
        wait_between_checks = 0.25

        logger.info("Checking if database is ready for connections.")

        while True:
            if time.monotonic() - start > wait_for:
                msg = f"Failed to connect to DB within {wait_for} seconds."
                logger.error(msg)
                exit(msg)

            conn = connections.create_connection(database)
            try:
                with conn.temporary_connection() as cursor:
                    cursor.execute("SELECT 1")
                logger.info("Successfully connected to the database.")
                break
            except OperationalError as e:
                logger.warning("Database not yet ready for connections.")
                logger.warning("Error was: %s: %s", e.__class__.__name__, e)

            time.sleep(wait_between_checks)

        if should_wait_for_migrations:
            logger.info("Checking for applied migrations.")

            while True:
                if time.monotonic() - start > wait_for:
                    msg = f"Didn't detect applied migrations for {wait_for} seconds."
                    logger.error(msg)
                    exit(msg)

                conn = connections[database]
                executor = MigrationExecutor(conn)
                if not executor.migration_plan(executor.loader.graph.leaf_nodes()):
                    logger.info("No pending migrations detected, good to go.")
                    return

                logger.warning("Migrations not yet applied.")
                time.sleep(wait_between_checks)
