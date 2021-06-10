from django.http import JsonResponse
from . import utils


def version_info(request):
    return JsonResponse(utils.get_version_info())
