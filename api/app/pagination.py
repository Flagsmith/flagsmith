import base64
import json
from collections import OrderedDict

from drf_yasg import openapi  # type: ignore[import-untyped]
from drf_yasg.inspectors import PaginatorInspector  # type: ignore[import-untyped]
from flag_engine.identities.models import IdentityModel
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999


class EdgeIdentityPaginationInspector(PaginatorInspector):  # type: ignore[misc]
    def get_paginator_parameters(self, paginator):  # type: ignore[no-untyped-def]
        """
        :param BasePagination paginator: the paginator
        :rtype: list[openapi.Parameter]
        """
        return [
            openapi.Parameter(
                "page_size",
                openapi.IN_QUERY,
                "Number of results to return per page.",
                required=False,
                type=openapi.TYPE_INTEGER,
            ),
            openapi.Parameter(
                "last_evaluated_key",
                openapi.IN_QUERY,
                "Used as the starting point for the page",
                required=False,
                type=openapi.TYPE_STRING,
            ),
        ]

    def get_paginated_response(self, paginator, response_schema):  # type: ignore[no-untyped-def]
        """
        :param BasePagination paginator: the paginator
        :param openapi.Schema response_schema: the response schema that must be paged.
        :rtype: openapi.Schema
        """

        return openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties=OrderedDict(
                (
                    (
                        "last_evaluated_key",
                        openapi.Schema(
                            type=openapi.TYPE_STRING,
                            x_nullable=True,
                        ),
                    ),
                    ("results", response_schema),
                )
            ),
            required=["results"],
        )


class EdgeIdentityPagination(CustomPagination):
    max_page_size = 100
    page_size = 100

    def paginate_queryset(self, dynamo_queryset, request, view=None):  # type: ignore[no-untyped-def]
        last_evaluated_key = dynamo_queryset.get("LastEvaluatedKey")
        if last_evaluated_key:
            self.last_evaluated_key = base64.b64encode(
                json.dumps(last_evaluated_key).encode()
            )

        return [
            IdentityModel.model_validate(identity_document)
            for identity_document in dynamo_queryset["Items"]
        ]

    def get_paginated_response(self, data) -> Response:  # type: ignore[no-untyped-def]
        """
        Note: "If the size of the Query result set is larger than 1 MB, ScannedCount
                and Count represent only a partial count of the total items"
        ref: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Query.html#Query.Count

        Tl;dr: there is no straightforward way to get the total number of items from dynamodb, that's why we don't
                include count in the response
        """
        return Response(
            OrderedDict(
                [
                    ("results", data),
                    (
                        "last_evaluated_key",
                        (
                            self.last_evaluated_key
                            if hasattr(self, "last_evaluated_key")
                            else None
                        ),
                    ),
                ]
            )
        )
