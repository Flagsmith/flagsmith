from contextlib import suppress

from django.core.exceptions import ObjectDoesNotExist
from rest_framework_api_key.permissions import KeyParser

from api_keys.models import MasterAPIKey

key_parser = KeyParser()


class MasterAPIKeyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        key = key_parser.get(request)
        with suppress(ObjectDoesNotExist):
            if key:
                key = MasterAPIKey.objects.get_from_key(key)
                request.master_api_key = key

        response = self.get_response(request)
        return response
