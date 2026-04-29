import pytest

from projects.code_references.services import _get_permalink
from projects.code_references.types import VCSProvider


@pytest.mark.parametrize(
    "repository_url",
    [
        "https://github.com/Flagsmith/flagsmith",
        "https://github.com/Flagsmith/flagsmith/",  # with trailing slash
    ],
)
def test_get_permalink__public_github_repository__returns_valid_url(
    repository_url: str,
) -> None:
    # Given / When
    result = _get_permalink(
        provider=VCSProvider.GITHUB,
        repository_url=repository_url,
        revision="revision-hash",
        file_path="path/to/file.py",
        line_number=10,
    )

    # Then
    assert result == (
        "https://github.com/Flagsmith/flagsmith/blob/revision-hash/path/to/file.py#L10"
    )


@pytest.mark.parametrize(
    "repository_url",
    [
        "https://github.flagsmith.com/flagsmith/backend",
        "https://github.flagsmith.com/flagsmith/backend/",  # with trailing slash
    ],
)
def test_get_permalink__private_github_repository__returns_valid_url(
    repository_url: str,
) -> None:
    # Given / When
    result = _get_permalink(
        provider=VCSProvider.GITHUB,
        repository_url=repository_url,
        revision="revision-hash",
        file_path="path/to/file.py",
        line_number=10,
    )

    # Then
    assert result == (
        "https://github.flagsmith.com/flagsmith/backend/blob/revision-hash/path/to/file.py#L10"
    )


@pytest.mark.parametrize(
    "repository_url",
    [
        "https://gitlab.com/Flagsmith/flagsmith",
        "https://gitlab.com/Flagsmith/flagsmith/",  # with trailing slash
    ],
)
def test_get_permalink__public_gitlab_repository__returns_valid_url(
    repository_url: str,
) -> None:
    # Given / When
    result = _get_permalink(
        provider=VCSProvider.GITLAB,
        repository_url=repository_url,
        revision="revision-hash",
        file_path="path/to/file.py",
        line_number=10,
    )

    # Then
    assert result == (
        "https://gitlab.com/Flagsmith/flagsmith/-/blob/revision-hash/path/to/file.py#L10"
    )


@pytest.mark.parametrize(
    "repository_url",
    [
        "https://gitlab.internal.flagsmith.com/flagsmith/backend",
        "https://gitlab.internal.flagsmith.com/flagsmith/backend/",  # with trailing slash
    ],
)
def test_get_permalink__private_gitlab_repository__returns_valid_url(
    repository_url: str,
) -> None:
    # Given / When
    result = _get_permalink(
        provider=VCSProvider.GITLAB,
        repository_url=repository_url,
        revision="revision-hash",
        file_path="path/to/file.py",
        line_number=10,
    )

    # Then
    assert result == (
        "https://gitlab.internal.flagsmith.com/flagsmith/backend/-/blob/revision-hash/path/to/file.py#L10"
    )
