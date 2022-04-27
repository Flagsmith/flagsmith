import base64
import json
import typing

from boto3.dynamodb.conditions import Key
from django.core.exceptions import ObjectDoesNotExist
from flag_engine.identities.builders import (
    build_identity_dict,
    build_identity_model,
)
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from app.pagination import EdgeIdentityPagination
from edge_api.identities.serializers import (
    EdgeIdentityFeatureStateSerializer,
    EdgeIdentitySerializer,
)
from environments.identities.models import Identity
from environments.models import Environment
from environments.permissions.permissions import NestedEnvironmentPermissions
from features.permissions import IdentityFeatureStatePermissions
from projects.exceptions import DynamoNotEnabledError


class EdgeIdentityViewSet(viewsets.ModelViewSet):
    serializer_class = EdgeIdentitySerializer
    permission_classes = [IsAuthenticated, NestedEnvironmentPermissions]
    pagination_class = EdgeIdentityPagination
    lookup_field = "identity_uuid"
    dynamo_identifier_search_functions = {
        "EQUAL": lambda identifier: Key("identifier").eq(identifier),
        "BEGINS_WITH": lambda identifier: Key("identifier").begins_with(identifier),
    }

    def initial(self, request, *args, **kwargs):
        environment = self.get_environment_from_request()
        if not environment.project.enable_dynamo_db:
            raise DynamoNotEnabledError()

        super().initial(request, *args, **kwargs)

    def _get_search_function_and_value(
        self,
        search_query: str,
    ) -> typing.Tuple[typing.Callable, str]:
        if search_query.startswith('"') and search_query.endswith('"'):
            return self.dynamo_identifier_search_functions[
                "EQUAL"
            ], search_query.replace('"', "")
        return self.dynamo_identifier_search_functions["BEGINS_WITH"], search_query

    def get_object(self):
        try:
            identity = Identity.dynamo_wrapper.get_item_from_uuid(
                self.kwargs["identity_uuid"]
            )
        except ObjectDoesNotExist as e:
            raise NotFound() from e
        return identity

    def get_queryset(self):
        page_size = self.pagination_class().get_page_size(self.request)
        previous_last_evaluated_key = self.request.GET.get("last_evaluated_key")
        search_query = self.request.query_params.get("q")
        start_key = None
        if previous_last_evaluated_key:
            start_key = json.loads(base64.b64decode(previous_last_evaluated_key))

        if not search_query:
            return Identity.dynamo_wrapper.get_all_items(
                self.kwargs["environment_api_key"], page_size, start_key
            )
        search_func, search_identifier = self._get_search_function_and_value(
            search_query
        )
        identity_documents = Identity.dynamo_wrapper.search_items_with_identifier(
            self.kwargs["environment_api_key"],
            search_identifier,
            search_func,
            page_size,
            start_key,
        )
        return identity_documents

    def get_environment_from_request(self):
        """
        Get environment object from URL parameters in request.
        """
        return Environment.objects.get(api_key=self.kwargs["environment_api_key"])

    def perform_destroy(self, instance):
        Identity.dynamo_wrapper.delete_item(instance["composite_key"])


class EdgeIdentityFeatureStateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IdentityFeatureStatePermissions]
    lookup_field = "featurestate_uuid"

    serializer_class = EdgeIdentityFeatureStateSerializer

    pagination_class = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        try:
            self.identity = self._get_identity_from_request()
        except ObjectDoesNotExist as e:
            raise NotFound() from e

    def _get_identity_from_request(self):
        """
        Get identity object from URL parameters in request.
        """

        identity_document = Identity.dynamo_wrapper.get_item_from_uuid(
            self.kwargs["edge_identity_identity_uuid"]
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
