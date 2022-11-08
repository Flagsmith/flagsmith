#!/usr/bin/env python
import os
import sys

# dummy change to see if E2E tests are broken in workflows

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
