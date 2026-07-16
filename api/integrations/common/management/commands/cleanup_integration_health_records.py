from datetime import timedelta

from django.core.management import BaseCommand, CommandParser
from django.utils import timezone

from integrations.common.models import IntegrationHealthRecord


class Command(BaseCommand):
    help = "Delete integration health records older than the specified number of days."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Delete records older than this many days (default: 30).",
        )

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        days = options["days"]
        cutoff = timezone.now() - timedelta(days=days)
        deleted, _ = IntegrationHealthRecord.objects.filter(
            created_at__lt=cutoff
        ).delete()
        self.stdout.write(
            f"Deleted {deleted} integration health record(s) older than {days} days."
        )
