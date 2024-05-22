import json
import logging

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from rest_framework.request import Request

from . import utils

logger = logging.getLogger(__name__)


def version_info(request: Request) -> JsonResponse:
    return JsonResponse(utils.get_version_info())


@csrf_exempt
def index(request):
    if request.method != "GET":
        logger.warning(
            "Invalid request made to %s with method %s", request.path, request.method
        )
        return HttpResponse(status=405, content_type="application/json")

    template = loader.get_template("webpack/index.html")
    return HttpResponse(template.render(request=request))


def project_overrides(request):
    """
    Build and return the dictionary of front-end relevant environment variables for configuration.
    It gets loaded as a script tag in the head of the browser when the frontend application starts up.
    """
    config_mapping_dict = {
        "amplitude": "AMPLITUDE_API_KEY",
        "api": "API_URL",
        "assetURL": "ASSET_URL",
        "crispChat": "CRISP_CHAT_API_KEY",
        "disableAnalytics": "DISABLE_ANALYTICS_FEATURES",
        "flagsmith": "FLAGSMITH_ON_FLAGSMITH_API_KEY",
        "flagsmithAnalytics": "FLAGSMITH_ANALYTICS",
        "flagsmithRealtime": "ENABLE_FLAGSMITH_REALTIME",
        "flagsmithClientAPI": "FLAGSMITH_ON_FLAGSMITH_API_URL",
        "ga": "GOOGLE_ANALYTICS_API_KEY",
        "fpr": "FIRST_PROMOTER_ID",
        "headway": "HEADWAY_API_KEY",
        "hideInviteLinks": "DISABLE_INVITE_LINKS",
        "linkedinPartnerTracking": "LINKEDIN_PARTNER_TRACKING",
        "maintenance": "MAINTENANCE_MODE",
        "mixpanel": "MIXPANEL_API_KEY",
        "preventEmailPassword": "PREVENT_EMAIL_PASSWORD",
        "preventSignup": "PREVENT_SIGNUP",
        "sentry": "SENTRY_API_KEY",
        "useSecureCookies": "USE_SECURE_COOKIES",
        "cookieSameSite": "COOKIE_SAME_SITE",
        "githubAppURL": "GITHUB_APP_URL",
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
