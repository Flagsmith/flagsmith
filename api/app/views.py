import json

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, JsonResponse
from django.template import loader

from . import utils


def version_info(request):
    return JsonResponse(utils.get_version_info())


def index(request):
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
        "flagsmith": "FLAGSMITH_ON_FLAGSMITH_API_URL",
        "flagsmithClientAPI": "FLAGSMITH_ON_FLAGSMITH_API_KEY",
        "ga": "GOOGLE_ANALYTICS_API_KEY",
        "linkedin_api_key": "LINKEDIN_API_KEY",
        "crispChat": "CRISP_CHAT_API_KEY",
        "mixpanel": "MIXPANEL_API_KEY",
        "sentry": "SENTRY_API_KEY",
        "amplitude": "AMPLITUDE_API_KEY",
    }

    project_overrides = {}

    for key, value in config_mapping_dict.items():
        settings_value = getattr(settings, value, None)
        if settings_value:
            project_overrides[key] = settings_value

    return HttpResponse("window.projectOverrides = " + json.dumps(project_overrides))
