from django.core.paginator import Paginator


def iterator_with_prefetch(queryset, chunk_size=2000):
    """
    Since queryset.iterator() does not support prefetch_related.
    Using Paginator() we can mimic the (somewhat)same behavior
    https://docs.djangoproject.com/en/3.2/ref/models/querysets/#iterator
    """
    if not queryset.query.order_by:
        # Paginator() throws a warning if there is no sorting attached to the queryset
        queryset = queryset.order_by("pk")

    paginator = Paginator(queryset, chunk_size)
    for index in range(paginator.num_pages):
        yield from paginator.get_page(index + 1)
