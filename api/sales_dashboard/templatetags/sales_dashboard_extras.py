import typing

from django.template.defaulttags import register


@register.filter
def get_item(dictionary: dict, key: typing.Any) -> typing.Any:
    return isinstance(dictionary, dict) and dictionary.get(key)


@register.simple_tag
def get_subcription_metadata(org) -> typing.Any:
    # TODO: implement this
    return {"max_seats": 100, "max_api_calls": 1000000}


@register.simple_tag
def query_transform(request, **kwargs):
    """
    Merges the existing query params with any new ones passed as kwargs.

    Note that we cannot simply use request.GET.update() as that merges lists rather
    than replacing the value entirely.
    """

    updated_query_params = request.GET.copy()

    for key, value in kwargs.items():
        updated_query_params[key] = value

    return updated_query_params.urlencode()
