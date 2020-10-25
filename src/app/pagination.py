from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 999
    page_size_query_param = "page_size"
    max_page_size = 999
