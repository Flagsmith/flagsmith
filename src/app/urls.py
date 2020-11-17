from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.http import HttpResponse

from users.views import password_reset_redirect

urlpatterns = [
    url(r'^api/v1/', include('api.urls.deprecated', namespace='api-deprecated')),
    url(r'^api/v1/', include('api.urls.v1', namespace='api-v1')),
    url(r'^admin/', admin.site.urls),
    url(r'^health', include('health_check.urls', namespace='health')),
    url(r'^sales-dashboard/', include('sales_dashboard.urls')),

    url(r'', lambda r: HttpResponse("Bullet Train API")),
    
    # this url is used to generate email content for the password reset workflow
    url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,'
        r'13}-[0-9A-Za-z]{1,20})/$',
        password_reset_redirect,
        name='password_reset_confirm'),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
