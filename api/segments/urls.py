from django.urls import path

from .views import get_segment_by_uuid

app_name = "segments"


urlpatterns = [
    path("get-by-uuid/<uuid:uuid>/", get_segment_by_uuid, name="get-segment-by-uuid"),
]
