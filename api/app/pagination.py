from collections import OrderedDict

from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999


class IdentityPagination(CustomPagination):
    def get_paginated_response_dynamo(self, data, count=None, *args, **kwargs):
        url = kwargs.get("request").build_absolute_uri()

        next_url = replace_query_param(
            url, "last_evaluated_key", kwargs.get("last_evaluated_key")
        )
        previous_url = replace_query_param(
            url,
            "last_evaluated_key",
            kwargs.get("previous_last_evaluated_key"),
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
