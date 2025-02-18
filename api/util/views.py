from rest_framework.generics import GenericAPIView

from environments.authentication import EnvironmentKeyAuthentication
from environments.permissions.permissions import EnvironmentKeyPermissions


class SDKAPIView(GenericAPIView):  # type: ignore[type-arg]
    permission_classes = (EnvironmentKeyPermissions,)
    authentication_classes = (EnvironmentKeyAuthentication,)
