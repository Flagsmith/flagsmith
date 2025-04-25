#!/usr/bin/env python
import os

from common.core.main import main

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings.local")

    main()
