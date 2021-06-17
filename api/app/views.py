from django.http import HttpResponse, JsonResponse
from django.template import loader

from . import utils


def version_info(request):
    return JsonResponse(utils.get_version_info())


def frontend_homepage(request):
    template = loader.get_template("frontend_homepage.html")
    context = {}
    return HttpResponse(template.render(context, request))
