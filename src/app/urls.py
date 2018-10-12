from django.conf.urls import url, include
from django.contrib import admin
from django.http import HttpResponse

from users.views import password_reset_redirect

urlpatterns = [
    url(r'^api/', include('api.urls', namespace='api')),
    url(r'^admin/', admin.site.urls),
    url(r'health', lambda r: HttpResponse("ok")),
    
    # this url is used to generate email content for the password reset workflow
    url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,'
        r'13}-[0-9A-Za-z]{1,20})/$',
        password_reset_redirect,
        name='password_reset_confirm'),
]
