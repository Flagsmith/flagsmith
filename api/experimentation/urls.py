from django.urls import path

from experimentation.views import WarehouseConnectionView

app_name = "experimentation"

urlpatterns = [
    path(
        "",
        WarehouseConnectionView.as_view(),
        name="warehouse-connections",
    ),
]
