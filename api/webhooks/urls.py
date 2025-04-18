from django.urls import path
from rest_framework import routers

from . import views

app_name = "webhooks"

router = routers.DefaultRouter()
router.register(r"", views.WebhookViewSet, basename="webhooks")

urlpatterns = router.urls