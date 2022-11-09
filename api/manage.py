#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

    # TODO: this is a bit hacky, can we improve it (perhaps we can override the migrate management command itself?)
    if len(sys.argv) > 1 and sys.argv[1] in (
        "migrate",
        "makemigrations",
        "migrate_schemas",
    ):
        os.environ.setdefault("USE_PRIMARY_DB_FOR_READ", "True")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
