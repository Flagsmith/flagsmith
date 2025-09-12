from django.urls import re_path

from .views import Teardown

app_name = "e2etests"


urlpatterns = [
    re_path(r"teardown/", Teardown.as_view(), name="teardown"),
]
