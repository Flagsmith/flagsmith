from django.urls import re_path

from .views import Teardown, UpdateSeats

app_name = "e2etests"


urlpatterns = [
    re_path(r"teardown/", Teardown.as_view(), name="teardown"),
    re_path(r"update-seats/", UpdateSeats.as_view(), name="update-seats"),
]
