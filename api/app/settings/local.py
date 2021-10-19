from app.settings.common import *  # noqa

ENABLE_AXES = False


ALLOWED_HOSTS.extend([".ngrok.io", "127.0.0.1", "localhost"])  # noqa

INSTALLED_APPS.extend(["debug_toolbar"])  # noqa

MIDDLEWARE.extend(["debug_toolbar.middleware.DebugToolbarMiddleware"])  # noqa

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


SWAGGER_SETTINGS["USE_SESSION_AUTH"] = False  # noqa

# Allow admin login with username and password
ENABLE_ADMIN_ACCESS_USER_PASS = True
