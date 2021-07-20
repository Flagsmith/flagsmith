import os

from app.settings.common import *

ALLOWED_HOSTS.extend([".ngrok.io", "127.0.0.1", "localhost"])

INSTALLED_APPS.extend(["debug_toolbar"])

MIDDLEWARE.extend(["debug_toolbar.middleware.DebugToolbarMiddleware"])

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# overwrite swagger settings to allow access without authentication
SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,
    "SHOW_REQUEST_HEADERS": True,
}
