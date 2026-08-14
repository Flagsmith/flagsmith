import pytest
from django.db import IntegrityError

from projects.models import Project
from projects.tags.models import Tag, TagType


def test_tag__duplicate_system_tag__raises_integrity_error(
    project: Project,
) -> None:
    # Given
    Tag.objects.create(
        label="Unhealthy",
        project=project,
        is_system_tag=True,
        type=TagType.UNHEALTHY,
    )

    # When / Then
    with pytest.raises(IntegrityError):
        Tag.objects.create(
            label="Unhealthy",
            project=project,
            is_system_tag=True,
            type=TagType.UNHEALTHY,
        )


def test_tag__duplicate_user_tag__created(
    project: Project,
) -> None:
    # Given
    Tag.objects.create(label="my tag", project=project)

    # When
    duplicate_tag = Tag.objects.create(label="my tag", project=project)

    # Then
    assert duplicate_tag.id is not None
