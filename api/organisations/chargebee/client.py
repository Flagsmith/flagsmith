from chargebee import Chargebee  # type: ignore[import-untyped]
from django.conf import settings

chargebee_client = Chargebee(
    api_key=settings.CHARGEBEE_API_KEY,
    site=settings.CHARGEBEE_SITE,
)
