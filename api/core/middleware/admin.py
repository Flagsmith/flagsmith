import logging

from core.helpers import get_ip_address_from_request
from django.conf import settings
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class AdminWhitelistMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        if request.path.startswith("/admin"):
            ip = get_ip_address_from_request(request)  # type: ignore[no-untyped-call]
            if (
                settings.ALLOWED_ADMIN_IP_ADDRESSES
                and ip not in settings.ALLOWED_ADMIN_IP_ADDRESSES
            ):
                # IP address not allowed!
                logger.info("Denying access to admin for ip address %s" % ip)
                raise PermissionDenied()

        return self.get_response(request)
