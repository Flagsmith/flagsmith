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
        "linkedin_api_key": settings.FRONTEND_LINKEDIN,
    }

    return HttpResponse(template.render(context, request))


def project_overrides(request):
    project_overrides = {}
    project_overrides["api"] = settings.FRONTEND_API_URL
    project_overrides["assetURL"] = settings.FRONTEND_ASSET_URL

    return HttpResponse("window.projectOverrides = " + json.dumps(project_overrides))
