from app.settings.production import *

SAML_REQUESTS_CACHE_LOCATION = "saml_requests_cache"

CACHES[SAML_REQUESTS_CACHE_LOCATION] = {
    "BACKEND": "django.core.cache.backends.db.DatabaseCache",
    "LOCATION": SAML_REQUESTS_CACHE_LOCATION,
}

INSTALLED_APPS += ["saml"]

SAML_ACCEPTED_TIME_DIFF = env.int("SAML_ACCEPTED_TIME_DIFF", default=60)

DJOSER["SERIALIZERS"]["current_user"] = "saml.serializers.SamlCurrentUserSerializer"
