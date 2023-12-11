import os

from app.settings.common import *  # noqa
from app.settings.common import REST_FRAMEWORK

# We dont want to track tests
ENABLE_TELEMETRY = False
MAX_PROJECTS_IN_FREE_PLAN = 10
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "login": "100/min",
    "mfa_code": "5/min",
    "invite": "10/min",
    "signup": "100/min",
    "user": "100000/day",
}

AWS_SSE_LOGS_BUCKET_NAME = "test_bucket"

# used by moto # ref https://github.com/getmoto/moto/issues/5941
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
