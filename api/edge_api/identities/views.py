from flag_engine.identities.builders import (
    build_identity_dict,
    build_identity_model,
)
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from edge_api.identities.serializers import EdgeIdentityFeatureStateSerializer
from environments.identities.models import Identity
from features.permissions import IdentityFeatureStatePermissions


class EdgeIdentityFeatureStateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IdentityFeatureStatePermissions]
    lookup_field = "featurestate_uuid"

    serializer_class = EdgeIdentityFeatureStateSerializer

    pagination_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.identity = self._get_identity_from_request()

    def _get_identity_from_request(self):
        """
        Get identity object from URL parameters in request.
        """

        identity_document = Identity.dynamo_wrapper.get_item_from_uuid(
            self.kwargs["environment_api_key"],
            self.kwargs["edge_identity_identity_uuid"],
        )
        return build_identity_model(identity_document)

    def get_object(self):
        featurestate_uuid = self.kwargs["featurestate_uuid"]
        try:
            featurestate = next(
                filter(
                    lambda fs: fs.featurestate_uuid == featurestate_uuid,
                    self.identity.identity_features,
                )
            )
        except StopIteration:
            raise NotFound()
        return featurestate

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.identity.identity_features, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        self.identity.identity_features.remove(instance)
        Identity.dynamo_wrapper.put_item(build_identity_dict(self.identity))
