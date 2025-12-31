import base64
import json
from collections import OrderedDict
from typing import Any

from drf_spectacular.utils import OpenApiParameter
from flag_engine.identities.models import IdentityModel
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999


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

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """
        Returns the OpenAPI schema for the paginated response.
        This is used by drf-spectacular to generate the schema.
        """
        return {
            "type": "object",
            "required": ["results"],
            "properties": {
                "last_evaluated_key": {
                    "type": "string",
                    "nullable": True,
                },
                "results": schema,
            },
        }


def get_edge_identity_pagination_parameters() -> list[OpenApiParameter]:
    """
    Returns the OpenAPI parameters for edge identity pagination.
    Use this function with @extend_schema(parameters=...) decorator.
    """
    return [
        OpenApiParameter(
            name="page_size",
            location=OpenApiParameter.QUERY,
            description="Number of results to return per page.",
            required=False,
            type=int,
        ),
        OpenApiParameter(
            name="last_evaluated_key",
            location=OpenApiParameter.QUERY,
            description="Used as the starting point for the page",
            required=False,
            type=str,
        ),
    ]
