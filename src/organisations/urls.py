from django.conf.urls import url, include
from rest_framework_nested import routers

from organisations.views import InviteViewSet
from users.views import FFAdminUserViewSet
from . import views


router = routers.DefaultRouter()
router.register(r'', views.OrganisationViewSet, base_name="organisation")

organisations_router = routers.NestedSimpleRouter(router, r'', lookup="organisation")
organisations_router.register(r'invites', InviteViewSet, base_name="organisation-invites")
organisations_router.register(r'users', FFAdminUserViewSet, base_name='organisation-users')

app_name = "organisations"

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^', include(organisations_router.urls))
]
