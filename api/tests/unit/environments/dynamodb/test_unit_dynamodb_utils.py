from decimal import Decimal

from environments.dynamodb.utils import estimate_document_size


def test_estimate_document_size__simple_document__returns_expected() -> None:
    # Given
    document = {"key": "value", "number": 42}

    # When
    result = estimate_document_size(document)

    # Then
    assert result == len('{"key":"value","number":42}'.encode())


def test_estimate_document_size__with_decimal_values__converts_to_numeric() -> None:
    # Given
    document = {"integer": Decimal("123"), "fractional": Decimal("1.5")}

    # When
    result = estimate_document_size(document)

    # Then
    assert result == len('{"integer":123,"fractional":1.5}'.encode())


def test_estimate_document_size__with_bytes__uses_raw_length() -> None:
    # Given
    binary_data = b"\x1f\x8b" * 10  # 20 bytes
    document = {"data": binary_data}

    # When
    result = estimate_document_size(document)

    # Then
    # The bytes are replaced with a string of the same length as the raw bytes.
    expected = len('{"data":"' + "0" * 20 + '"}')
    assert result == expected


def test_estimate_document_size__nested_document__returns_expected() -> None:
    # Given
    document = {
        "outer": {
            "inner": "value",
            "list": [Decimal("1"), Decimal("2")],
        },
        "flag": True,
        "empty": None,
    }

    # When
    result = estimate_document_size(document)

    # Then
    assert result == len(
        '{"outer":{"inner":"value","list":[1,2]},"flag":true,"empty":null}'.encode()
    )


def test_estimate_document_size__with_unknown_type__assumes_str() -> None:
    # Given
    document = {"value": object()}

    # When
    result = estimate_document_size(document)

    # Then
    assert result == 42


def test_estimate_document_size__empty_document__returns_expected() -> None:
    # Given
    document: dict[str, object] = {}

    # When
    result = estimate_document_size(document)

    # Then
    assert result == len("{}".encode())
