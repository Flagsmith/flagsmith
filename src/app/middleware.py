from django.conf import settings
from django.core.exceptions import PermissionDenied

from util.logging import get_logger

logger = get_logger(__name__)


class AdminWhitelistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin'):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
            if settings.ALLOWED_ADMIN_IP_ADDRESSES and ip not in settings.ALLOWED_ADMIN_IP_ADDRESSES:
                # IP address not allowed!
                logger.info('Denying access to admin for ip address %s' % ip)
                raise PermissionDenied()

        return self.get_response(request)
