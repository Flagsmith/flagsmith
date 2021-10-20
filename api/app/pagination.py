from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999


class IdentityPagination(CustomPagination):
    def get_paginated_response_dynamo(
        self,
        data,
        request,
        count,
        last_evaluated_key=None,
        previous_last_evaluated_key=None,
    ):
        url = request.build_absolute_uri()

        next_url = (
            replace_query_param(url, "last_evaluated_key", last_evaluated_key)
            if last_evaluated_key
            else None
        )
        previous_url = (
            replace_query_param(url, "last_evaluated_key", previous_last_evaluated_key)
            if previous_last_evaluated_key
            else None
        )
        return Response(
            OrderedDict(
                [
                    ("count", count),
                    ("results", data),
                    ("previous", previous_url),
                    ("next", next_url),
                ]
            )
        )
