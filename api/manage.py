#!/usr/bin/env python
import os
import sys

from common.core.main import main

if __name__ == "__main__":
    # Backwards compatibility for task-processor health checks
    # See https://github.com/Flagsmith/flagsmith-task-processor/issues/24
    if "checktaskprocessorthreadhealth" in sys.argv:
        import scripts.healthcheck

        scripts.healthcheck.main()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

    main()
