import typing

from django.template.defaulttags import register


@register.filter
def get_item(dictionary: dict, key: typing.Any) -> typing.Any:
    return isinstance(dictionary, dict) and dictionary.get(key)
