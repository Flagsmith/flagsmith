from collections import OrderedDict

from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class ChannelListPagination(CursorPagination):
    page_size_query_param = "page_size"

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        cursor = request.GET.get("cursor", None)
        response = queryset.get_channels_data(limit=page_size, cursor=cursor)
        self.next_cursor = response.cursor
        return response.channels

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [("cursor", self.next_cursor), ("results", data), ("count", len(data))]
            )
        )
