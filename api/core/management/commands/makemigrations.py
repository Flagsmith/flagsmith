from django.core.management import CommandError
from django.core.management.commands.makemigrations import (
    Command as MakeMigrationsCommand,
)


class Command(MakeMigrationsCommand):
    """
    Customise the makemigrations command to enforce use of `--name/-n` argument.
    """

    def handle(self, *app_labels, **options):
        if not options.get("name"):
            raise CommandError("--name/-n is a required argument")

        return super().handle(*app_labels, **options)
