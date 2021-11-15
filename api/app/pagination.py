import base64
import json
from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999


class IdentityPagination(CustomPagination):
    last_evaluated_key = None
    previous_last_evaluated_key = None
    dynamodb_count = None

    def set_pagination_state_dynamo(self, dynamo_queryset, request) -> None:
        self.previous_last_evaluated_key = request.GET.get("last_evaluated_key")
        self.request = request
        self.dynamodb_count = dynamo_queryset["Count"]

        last_evaluated_key = dynamo_queryset.get("LastEvaluatedKey")
        if last_evaluated_key:
            self.last_evaluated_key = base64.b64encode(
                json.dumps(last_evaluated_key).encode()
            )

    def next_link_dynamo(self) -> str:
        url = self.request.build_absolute_uri()
        next_url = (
            replace_query_param(url, "last_evaluated_key", self.last_evaluated_key)
            if self.last_evaluated_key
            else None
        )
        return next_url

    def previous_link_dynamo(self) -> str:
        url = self.request.build_absolute_uri()
        previous_url = (
            replace_query_param(
                url, "last_evaluated_key", self.previous_last_evaluated_key
            )
            if self.previous_last_evaluated_key
            else None
        )
        return previous_url

    def get_paginated_response_dynamo(self, data) -> Response:
        return Response(
            OrderedDict(
                [
                    ("count", self.dynamodb_count),
                    ("results", data),
                    ("previous", self.previous_link_dynamo()),
                    ("next", self.next_link_dynamo()),
                ]
            )
        )
