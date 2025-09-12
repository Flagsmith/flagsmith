import typing

from django.template.defaulttags import register


@register.filter  # type: ignore[misc]
def get_item(dictionary: dict, key: typing.Any) -> typing.Any:  # type: ignore[type-arg]
    return isinstance(dictionary, dict) and dictionary.get(key)


@register.simple_tag
def query_transform(request, **kwargs):  # type: ignore[no-untyped-def]
    """
    Merges the existing query params with any new ones passed as kwargs.

    Note that we cannot simply use request.GET.update() as that merges lists rather
    than replacing the value entirely.
    """

    updated_query_params = request.GET.copy()

    for key, value in kwargs.items():
        updated_query_params[key] = value

    return updated_query_params.urlencode()
