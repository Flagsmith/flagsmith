from app.settings.common import *

ENABLE_AXES = False


ALLOWED_HOSTS.extend([".ngrok.io", "127.0.0.1", "localhost"])

INSTALLED_APPS.extend(["debug_toolbar", "django_extensions"])

MIDDLEWARE.extend(["debug_toolbar.middleware.DebugToolbarMiddleware"])

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


SPECTACULAR_SETTINGS["SERVE_AUTHENTICATION"] = (
    "rest_framework.authentication.SessionAuthentication",
)

# Allow admin login with username and password
ENABLE_ADMIN_ACCESS_USER_PASS = True

SKIP_MIGRATION_TESTS = True
