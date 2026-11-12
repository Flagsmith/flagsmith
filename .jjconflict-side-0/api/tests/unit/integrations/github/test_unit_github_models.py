from integrations.github.constants import GitHubTag
from integrations.github.models import GithubConfiguration, GitHubRepository
from projects.models import Project
from projects.tags.models import Tag, TagType


def test_create_github_tags__existing_tag_with_drifted_attributes__reuses_existing_tag(
    github_configuration: GithubConfiguration,
    project: Project,
) -> None:
    # Given
    # a pre-existing system tag whose colour and description differ
    # from the current defaults
    existing_tag = Tag.objects.create(
        label=GitHubTag.PR_OPEN.value,
        project=project,
        is_system_tag=True,
        type=TagType.GITHUB,
        color="#123456",
        description="A drifted description",
    )

    # When
    GitHubRepository.objects.create(
        github_configuration=github_configuration,
        repository_owner="repositoryownertest",
        repository_name="repositorynametest",
        project=project,
        tagging_enabled=True,
    )

    # Then - the hook reuses the existing tag instead of creating a duplicate
    github_tags = Tag.objects.filter(project=project, type=TagType.GITHUB)
    assert github_tags.count() == len(GitHubTag)
    assert github_tags.get(label=GitHubTag.PR_OPEN.value).id == existing_tag.id
