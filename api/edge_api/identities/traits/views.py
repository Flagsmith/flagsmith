import marshmallow
from flag_engine.api.schemas import APITraitSchema
from flag_engine.identities.builders import build_identity_dict
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from edge_api.identities.views_mixins import GetIdentityMixin
from environments.identities.models import Identity

from .permissions import EnvironmentIdentityTraitsPermission

trait_schema = APITraitSchema()


class EdgeIdentityTraitsViewSet(viewsets.ModelViewSet, GetIdentityMixin):
    lookup_field = "trait_key"
    permission_classes = [EnvironmentIdentityTraitsPermission]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.identity = self.get_identity_from_request_or_404()

    def get_object(self):
        trait_key = self.kwargs["trait_key"]
        try:
            trait = next(
                filter(
                    lambda trait: trait.trait_key == trait_key,
                    self.identity.identity_traits,
                )
            )
        except StopIteration:
            raise NotFound()
        return trait

    def list(self, request, *args, **kwargs):
        data = {"traits": trait_schema.dump(self.identity.identity_traits, many=True)}
        return Response(data=data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        data = trait_schema.dump(instance)
        return Response(data)

    def perform_destroy(self, instance):
        self.identity.identity_traits.remove(instance)
        self._save()

    def create(self, request, *args, **kwargs):
        data = self._create_or_update(request)
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
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
