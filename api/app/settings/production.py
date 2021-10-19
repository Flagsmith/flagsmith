from app.settings.common import *

REST_FRAMEWORK["PAGE_SIZE"] = 999

# Needed by Elastic Beanstalk to correctly identify incoming protocol
# https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html#x-forwarded-proto
SECURE_PROXY_SSL_HEADER = ("X-Forwarded-Proto", "https")
