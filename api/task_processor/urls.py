from django.urls import path

from task_processor.views import monitoring

app_name = "task_processor"

urlpatterns = [path("monitoring/", monitoring, name="monitoring")]
