from common.core.urls import urlpatterns as core_urlpatterns
from django.urls import include, path

urlpatterns = [
    *core_urlpatterns,
    path("processor/", include("task_processor.urls")),
]
