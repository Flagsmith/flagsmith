from environments.models import Environment
from features.models import Feature
from features.versioning.models import EnvironmentFeatureVersion
from projects.tags.models import Tag, TagType
from users.models import FFAdminUser


def test_environment_feature_version_published__stale_tag__removes_only_stale_tag(
    feature: Feature,
    environment_v2_versioning: Environment,
    admin_user: FFAdminUser,
    tag_one: Tag,
) -> None:
    # Given
    stale_tag = Tag.objects.create(
        label="Stale",
        project=feature.project,
        is_system_tag=True,
        type=TagType.STALE,
    )
    unhealthy_tag = Tag.objects.create(
        label="Unhealthy",
        project=feature.project,
        is_system_tag=True,
        type=TagType.UNHEALTHY,
    )
    feature.tags.add(stale_tag, unhealthy_tag, tag_one)

    version = EnvironmentFeatureVersion.objects.create(
        environment=environment_v2_versioning, feature=feature
    )

    # When
    version.publish(admin_user)

    # Then
    assert set(feature.tags.all()) == {unhealthy_tag, tag_one}
