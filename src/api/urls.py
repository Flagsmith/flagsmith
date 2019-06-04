from django.conf.urls import url, include

from features.views import SDKFeatureStates
from environments.views import SDKIdentities, SDKTraits
from segments.views import SDKSegments


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

        # TODO: remove identifier from URL and move to e.g. GET parameter
        # Client SDK urls
        url(r"^flags/(?P<identifier>[\w $&+,:;=?@#|'<>.-^*()%!]+)", SDKFeatureStates.as_view()),
        url(r'^flags/', SDKFeatureStates.as_view()),

        url(r"^identities/(?P<identifier>[\w $&+,:;=?@#|'<>.-^*()%!]+)/traits/(?P<trait_key>[-\w.]+)", SDKTraits.as_view()),
        url(r"^identities/(?P<identifier>[\w $&+,:;=?@#|'<>.-^*()%!]+)/", SDKIdentities.as_view()),

        url(r'^segments/', SDKSegments.as_view()),

        # API documentation
        url(r'^docs/', include('docs.urls', namespace='docs'))
    ], namespace='v1'))
]