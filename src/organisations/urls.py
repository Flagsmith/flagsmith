from django.conf.urls import url, include
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()
router.register(r'', views.OrganisationViewSet, base_name="organisation")

app_name = "organisations"

urlpatterns = [
    url(r'^', include(router.urls)),
]
