from django.contrib.staticfiles.storage import staticfiles_storage
from django.http import HttpResponse, JsonResponse

from . import utils


def version_info(request):
    return JsonResponse(utils.get_version_info())


def index(request):
    index_file = open(staticfiles_storage.path("index.html"), "r")
    return HttpResponse(index_file.read())
