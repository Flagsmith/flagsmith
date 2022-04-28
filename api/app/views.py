import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt

from . import utils

logger = logging.getLogger(__name__)


def version_info(request):
    return JsonResponse(utils.get_version_info())


@csrf_exempt
def index(request):
    if not request.method == "GET":
        logger.warning(
            "Invalid request made to %s with method %s", request.path, request.method
        )
        return HttpResponse(status=415, content_type="application/json")

    template = loader.get_template("webpack/index.html")
    context = {
        "linkedin_api_key": settings.LINKEDIN_API_KEY,
    }
    return HttpResponse(template.render(context, request))


def project_overrides(request):
    """
    Build and return the dictionary of front-end relevant environment variables for configuration.
    It gets loaded as a script tag in the head of the browser when the frontend application starts up.
    """
    config_mapping_dict = {
        "api": "API_URL",
        "assetURL": "ASSET_URL",
        "maintenance": "MAINTENANCE_MODE",
        "preventSignup": "PREVENT_SIGNUP",
        "disableInflux": "DISABLE_INFLUXDB_FEATURES",
        "flagsmithAnalytics": "FLAGSMITH_ANALYTICS",
        "flagsmith": "FLAGSMITH_ON_FLAGSMITH_API_KEY",
        "flagsmithClientAPI": "FLAGSMITH_ON_FLAGSMITH_API_URL",
        "ga": "GOOGLE_ANALYTICS_API_KEY",
        "linkedin_api_key": "LINKEDIN_API_KEY",
        "crispChat": "CRISP_CHAT_API_KEY",
        "mixpanel": "MIXPANEL_API_KEY",
        "sentry": "SENTRY_API_KEY",
        "amplitude": "AMPLITUDE_API_KEY",
    }

    override_data = {
        key: getattr(settings, value)
        for key, value in config_mapping_dict.items()
        if getattr(settings, value, None) is not None
    }

    return HttpResponse(
        content="window.projectOverrides = " + json.dumps(override_data),
        content_type="application/javascript",
    )
