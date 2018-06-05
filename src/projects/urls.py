from django.conf.urls import url, include
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()
router.register(r'', views.ProjectViewSet, base_name="project")

app_name = "projects"

urlpatterns = [
    url(r'^', include(router.urls)),
]
