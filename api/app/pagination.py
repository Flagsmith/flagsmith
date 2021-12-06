import base64
import json
from collections import OrderedDict

from flag_engine.identities.builders import build_identity_model
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999


class EdgeIdentityPagination(CustomPagination):
    def paginate_queryset(self, dynamo_queryset, request, view=None):
        self.previous_last_evaluated_key = request.GET.get("last_evaluated_key")
        self.request = request
        last_evaluated_key = dynamo_queryset.get("LastEvaluatedKey")
        if last_evaluated_key:
            self.last_evaluated_key = base64.b64encode(
                json.dumps(last_evaluated_key).encode()
            )

        return [
            build_identity_model(identity_document)
            for identity_document in dynamo_queryset["Items"]
        ]

    def get_next_link(self) -> str:
        url = self.request.build_absolute_uri()
        next_url = (
            replace_query_param(url, "last_evaluated_key", self.last_evaluated_key)
            if hasattr(self, "last_evaluated_key")
            else None
        )
        return next_url

    def get_previous_link(self) -> str:
        url = self.request.build_absolute_uri()
        previous_url = (
            replace_query_param(
                url, "last_evaluated_key", self.previous_last_evaluated_key
            )
            if self.previous_last_evaluated_key
            else None
        )
        return previous_url

    def get_paginated_response(self, data) -> Response:
        return Response(
            OrderedDict(
                [
                    ("results", data),
                    ("previous", self.get_previous_link()),
                    ("next", self.get_next_link()),
                ]
            )
        )
