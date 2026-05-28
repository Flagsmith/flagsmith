from projects.tags.models import TagType


def test_tag_type__azure_devops__has_value() -> None:
    # Given / When / Then
    assert TagType.AZURE_DEVOPS.value == "AZURE_DEVOPS"


def test_tag_type__members__include_existing_and_azure() -> None:
    # Given
    values = {member.value for member in TagType}

    # Then
    assert values == {"NONE", "STALE", "GITHUB", "UNHEALTHY", "GITLAB", "AZURE_DEVOPS"}
