#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # Backwards compatibility for task-processor health checks
    # See https://github.com/Flagsmith/flagsmith-task-processor/issues/24
    if "checktaskprocessorthreadhealth" in sys.argv:
        import scripts.healthcheck

        scripts.healthcheck.main()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        )

    execute_from_command_line(sys.argv)
