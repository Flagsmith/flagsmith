from rest_framework.generics import GenericAPIView

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions


class SDKAPIView(GenericAPIView):
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)