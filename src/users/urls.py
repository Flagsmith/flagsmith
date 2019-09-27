from django.conf import settings
from django.conf.urls import url

from .views import AdminInitView, join_organisation

app_name = "users"

urlpatterns = [
    url(r'^join/(?P<invite_hash>\w+)/', join_organisation, name='user-join-organisation'),
]
if settings.ALLOW_ADMIN_INITIATION_VIA_URL:
    urlpatterns.insert(0, url(r'init/', AdminInitView.as_view()))
