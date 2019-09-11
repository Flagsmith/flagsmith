from django.conf.urls import url, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, authentication, routers

from environments.views import SDKIdentitiesDeprecated, SDKTraitsDeprecated, SDKIdentities, SDKTraits
from features.views import SDKFeatureStates
from environments.views import SDKIdentities, SDKTraits
from segments.views import SDKSegments

schema_view = get_schema_view(
    openapi.Info(
        title="Bullet Train API",
        default_version='v1',
        description="",
        license=openapi.License(name="BSD License"),
        contact=openapi.Contact(email="supprt@bullet-train.io"),
    ),
    public=False,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(authentication.SessionAuthentication,)
)

traits_router = routers.DefaultRouter()
traits_router.register(r'', SDKTraits, basename='sdk-traits')

current_urls = [
    url(r'^organisations/', include('organisations.urls')),
    url(r'^projects/', include('projects.urls')),
    url(r'^environments/', include('environments.urls')),
    url(r'^users/', include('users.urls')),
    url(r'^auth/', include('rest_auth.urls')),
    url(r'^auth/register/', include('rest_auth.registration.urls')),
    url(r'^account/', include('allauth.urls')),
    url(r'^e2etests/', include('e2etests.urls')),
    url(r'^features/', include('features.urls')),

    # Client SDK urls
    url(r'^flags/$', SDKFeatureStates.as_view()),
    url(r'^identities/$', SDKIdentities.as_view(), name='sdk-identities'),
    url(r'^traits/', include(traits_router.urls)),
    url(r'^segments/$', SDKSegments.as_view()),

    # API documentation
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^docs/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui')
]

deprecated_urls = [
    url(r'^identities/(?P<identifier>[-\w@%.]+)/traits/(?P<trait_key>[-\w.]+)', SDKTraitsDeprecated.as_view()),
    url(r'^identities/(?P<identifier>[-\w@%.]+)/', SDKIdentitiesDeprecated.as_view()),
    url(r'^flags/(?P<identifier>[-\w@%.]+)', SDKFeatureStates.as_view())
]

urlpatterns = [
    url(r'^v1/', include(deprecated_urls, namespace='deprecated')),
    url(r'^v1/', include(current_urls, namespace='v1')),
]