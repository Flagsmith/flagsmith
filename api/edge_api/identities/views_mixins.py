from django.core.exceptions import ObjectDoesNotExist
from flag_engine.identities.builders import build_identity_model
from rest_framework.exceptions import NotFound

from environments.identities.models import Identity


class GetIdentityMixin:
    def get_identity_from_request_or_404(self):
        """
        Get identity object from URL parameters in request.
        """

        try:
            identity_document = Identity.dynamo_wrapper.get_item_from_uuid(
                self.kwargs["environment_api_key"],
                self.kwargs["edge_identity_identity_uuid"],
            )
        except ObjectDoesNotExist as e:
            raise NotFound() from e
        return build_identity_model(identity_document)
