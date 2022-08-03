from django.urls import path

from task_processor.views import monitoring

urlpatterns = [path("monitoring/", monitoring)]
