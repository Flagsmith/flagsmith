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
def test_get_permalink_generates_valid_public_github_url(
    repository_url: str,
) -> None:
    # When
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
        "https://github.flagsmith.com/backend",
        "https://github.flagsmith.com/backend/",  # with trailing slash
    ],
)
def test_get_permalink_generates_valid_private_github_url(
    repository_url: str,
) -> None:
    # When
    result = _get_permalink(
        provider=VCSProvider.GITHUB,
        repository_url=repository_url,
        revision="revision-hash",
        file_path="path/to/file.py",
        line_number=10,
    )

    # Then
    assert result == (
        "https://github.flagsmith.com/backend/blob/revision-hash/path/to/file.py#L10"
    )
