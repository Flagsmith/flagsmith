from django.conf.urls import url

from docs.views import schema_view

urlpatterns = [
    url(r'^', schema_view, name='index')
]