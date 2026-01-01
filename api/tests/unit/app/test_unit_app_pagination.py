from drf_spectacular.utils import OpenApiParameter

from app.pagination import get_edge_identity_pagination_parameters


def test_get_edge_identity_pagination_parameters__returns_expected() -> None:
    # When
    parameters = get_edge_identity_pagination_parameters()

    # Then
    assert len(parameters) == 2
    assert all(isinstance(param, OpenApiParameter) for param in parameters)

    page_size_param = parameters[0]
    assert page_size_param.name == "page_size"
    assert page_size_param.location == OpenApiParameter.QUERY
    assert page_size_param.required is False
    assert page_size_param.type is int

    last_evaluated_key_param = parameters[1]
    assert last_evaluated_key_param.name == "last_evaluated_key"
    assert last_evaluated_key_param.location == OpenApiParameter.QUERY
    assert last_evaluated_key_param.required is False
    assert last_evaluated_key_param.type is str
