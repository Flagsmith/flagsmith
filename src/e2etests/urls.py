from django.conf.urls import url

from .views import Teardown

app_name = "e2etests"


urlpatterns = [
    url(r'teardown/', Teardown.as_view(), name='teardown')
]