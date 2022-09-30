import typing

from django import template
from django.template.defaulttags import register

from organisations.subscriptions.service import get_subscription_metadata


@register.filter
def get_item(dictionary: dict, key: typing.Any) -> typing.Any:
    return isinstance(dictionary, dict) and dictionary.get(key)


class LoadSubcriptionMetadataNode(template.Node):
    def __init__(self, org):
        self.org = template.Variable(org)

    def render(self, context):
        org = self.org.resolve(context)
        context["subscription_metadata"] = get_subscription_metadata(org)
        return ""


@register.tag
def load_subcription_metadata(parser, token) -> typing.Any:
    try:
        _, org = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    return LoadSubcriptionMetadataNode(org)


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
