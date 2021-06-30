import json

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, JsonResponse

from . import utils


def version_info(request):
    return JsonResponse(utils.get_version_info())


def index(request):
    index_file = open(staticfiles_storage.path("index.html"), "r")
    return HttpResponse(index_file.read())


def project_overrides(request):
    project_overrides = {}
    project_overrides["api"] = settings.FRONTEND_API_URL
    project_overrides["assetURL"] = settings.FRONTEND_ASSET_URL

    return HttpResponse("window.projectOverrides = " + json.dumps(project_overrides))
