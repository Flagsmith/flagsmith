from django.conf.urls import url, include

from features.views import SDKFeatureStates

urlpatterns = [
    url(r'^v1/', include([
        url(r'^organisations/', include('organisations.urls')),
        url(r'^projects/', include('projects.urls')),
        url(r'^environments/', include('environments.urls')),
        url(r'^users/', include('users.urls')),
        url(r'^auth/', include('rest_auth.urls')),
        url(r'^auth/register/', include('rest_auth.registration.urls')),
        url(r'^account/', include('allauth.urls')),
        url(r'^e2etests/', include('e2etests.urls')),

        # Client SDK urls
        url(r'^flags/(?P<identifier>\w+)', SDKFeatureStates.as_view()),
        url(r'^flags/', SDKFeatureStates.as_view()),

        # API documentation
        url(r'^docs/', include('docs.urls', namespace='docs'))
    ], namespace='v1'))
]
