from django.conf import settings


def is_edge_enabled() -> bool:
    return bool(settings.EDGE_ENABLED)
