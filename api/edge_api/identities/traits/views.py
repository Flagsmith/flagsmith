import marshmallow
from drf_yasg2.utils import swagger_auto_schema
from flag_engine.api.schemas import APITraitSchema
from flag_engine.identities.builders import build_identity_dict
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from edge_api.identities.views_mixins import GetIdentityMixin
from environments.identities.models import Identity

from .permissions import EnvironmentIdentityTraitsPermission
from .serializers import EdgeIdentityTraitsResponseSerializer

trait_schema = APITraitSchema()


class EdgeIdentityTraitsViewSet(viewsets.ViewSet, GetIdentityMixin):
    permission_classes = [EnvironmentIdentityTraitsPermission]

    serializer_class = EdgeIdentityTraitsResponseSerializer

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.identity = self.get_identity_from_request_or_404()

    @swagger_auto_schema(
        responses={200: EdgeIdentityTraitsResponseSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        data = trait_schema.dump(self.identity.identity_traits, many=True)
        return Response(data=data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post", "put"], url_path="create-or-update")
    def create_or_update(self, request, *args, **kwargs):
        data = self._create_or_update(request)
        return Response(data, status=status.HTTP_200_OK)

    def _create_or_update(self, request):
        try:
            trait = trait_schema.load(request.data)
        except marshmallow.ValidationError as validation_error:
            raise ValidationError(validation_error) from validation_error
        self.identity.update_traits([trait])
        self._save()
        return trait_schema.dump(trait)

    def _save(self):
        Identity.dynamo_wrapper.put_item(build_identity_dict(self.identity))
