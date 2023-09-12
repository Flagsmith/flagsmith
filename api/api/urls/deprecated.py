from django.urls import re_path

from environments.identities.traits.views import SDKTraitsDeprecated
from environments.identities.views import SDKIdentitiesDeprecated
from features.views import SDKFeatureStates

app_name = "deprecated"

urlpatterns = [
    re_path(
        r"^identities/(?P<identifier>[-\w@%.]+)/traits/(?P<trait_key>[-\w.]+)$",
        SDKTraitsDeprecated.as_view(),
    ),
    re_path(r"^identities/(?P<identifier>[-\w@%.]+)/", SDKIdentitiesDeprecated.as_view()),
    re_path(r"^flags/(?P<identifier>[-\w@%.]+)$", SDKFeatureStates.as_view()),
]
