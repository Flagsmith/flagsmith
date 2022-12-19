from django.conf.urls import url

from .views import Teardown, UpdateSeats

app_name = "e2etests"


urlpatterns = [
    url(r"teardown/", Teardown.as_view(), name="teardown"),
    url(r"update-seats/", UpdateSeats.as_view(), name="update-seats"),
]
