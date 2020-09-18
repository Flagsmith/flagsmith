from django.conf.urls import url

from environments.identities.traits.views import SDKTraitsDeprecated
from environments.identities.views import SDKIdentitiesDeprecated
from features.views import SDKFeatureStates

app_name = 'deprecated'

urlpatterns = [
    url(r'^identities/(?P<identifier>[-\w@%.]+)/traits/(?P<trait_key>[-\w.]+)', SDKTraitsDeprecated.as_view()),
    url(r'^identities/(?P<identifier>[-\w@%.]+)/', SDKIdentitiesDeprecated.as_view()),
    url(r'^flags/(?P<identifier>[-\w@%.]+)', SDKFeatureStates.as_view())
]