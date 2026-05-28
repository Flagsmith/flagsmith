from projects.tags.models import TagType


def test_tag_type__azure_devops__has_value() -> None:
    # Given / When / Then
    assert TagType.AZURE_DEVOPS.value == "AZURE_DEVOPS"


def test_tag_type__members__include_existing_and_azure() -> None:
    # Given
    values = {member.value for member in TagType}

    # Then
    assert values == {"NONE", "STALE", "GITHUB", "UNHEALTHY", "GITLAB", "AZURE_DEVOPS"}


def test_tag_type_field__choices__include_azure_devops() -> None:
    # Given
    from projects.tags.models import Tag

    field = Tag._meta.get_field("type")
    assert field.choices is not None  # type narrowing for mypy strict

    # When
    choice_values = {value for value, _label in field.choices}

    # Then
    assert "AZURE_DEVOPS" in choice_values
