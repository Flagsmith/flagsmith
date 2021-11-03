from app.settings.common import *

REST_FRAMEWORK["PAGE_SIZE"] = 999

# Needed by Elastic Beanstalk to correctly identify incoming protocol
# https://docs.aws.amazon.com/elasticloadbalancing/latest/application/x-forwarded-headers.html#x-forwarded-proto
# Although in our case SSL termination happens in Cloudfront so the header is named as below.
SECURE_PROXY_SSL_HEADER = ("HTTP_CLOUDFRONT_FORWARDED_PROTO", "https")
