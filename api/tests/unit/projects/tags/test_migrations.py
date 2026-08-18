import pytest
from django.conf import settings as test_settings
from django_test_migrations.migrator import Migrator


@pytest.mark.skipif(
    test_settings.SKIP_MIGRATION_TESTS is True,
    reason="Skip migration tests to speed up tests where necessary",
)
def test_unique_system_tags__duplicate_system_tags__deduplicated_and_features_repointed(
    migrator: Migrator,
) -> None:
    # Given
    old_state = migrator.apply_initial_migration(("tags", "0009_add_gitlab_tag_type"))
    Organisation = old_state.apps.get_model("organisations", "Organisation")
    Project = old_state.apps.get_model("projects", "Project")
    Tag = old_state.apps.get_model("tags", "Tag")
    Feature = old_state.apps.get_model("features", "Feature")

    organisation = Organisation.objects.create(name="Test Organisation")
    project = Project.objects.create(name="Test Project", organisation=organisation)

    # A system tag duplicated twice
    canonical_tag = Tag.objects.create(
        project=project, label="PR Open", type="GITHUB", is_system_tag=True
    )
    first_duplicate_tag = Tag.objects.create(
        project=project, label="PR Open", type="GITHUB", is_system_tag=True
    )
    second_duplicate_tag = Tag.objects.create(
        project=project, label="PR Open", type="GITHUB", is_system_tag=True
    )

    # A non-duplicated system tag
    unique_system_tag = Tag.objects.create(
        project=project, label="Unhealthy", type="UNHEALTHY", is_system_tag=True
    )

    # Duplicate user tags, which are allowed to collide
    Tag.objects.create(project=project, label="user tag")
    Tag.objects.create(project=project, label="user tag")

    # A feature tagged with a duplicate only
    feature_with_duplicate = Feature.objects.create(
        name="feature_with_duplicate", project=project
    )
    feature_with_duplicate.tags.add(first_duplicate_tag)

    # A feature tagged with both the canonical tag and a duplicate
    feature_with_both = Feature.objects.create(
        name="feature_with_both", project=project
    )
    feature_with_both.tags.add(canonical_tag, second_duplicate_tag)

    # When
    new_state = migrator.apply_tested_migration(("tags", "0010_unique_system_tags"))

    # Then
    # only the oldest duplicate survives
    NewTag = new_state.apps.get_model("tags", "Tag")
    NewFeature = new_state.apps.get_model("features", "Feature")

    surviving_tag = NewTag.objects.get(
        project_id=project.id, label="PR Open", type="GITHUB", is_system_tag=True
    )
    assert surviving_tag.id == canonical_tag.id

    # and features previously tagged with a duplicate point at the surviving tag
    assert list(
        NewFeature.objects.get(id=feature_with_duplicate.id).tags.values_list(
            "id", flat=True
        )
    ) == [canonical_tag.id]
    assert list(
        NewFeature.objects.get(id=feature_with_both.id).tags.values_list(
            "id", flat=True
        )
    ) == [canonical_tag.id]

    # and unrelated tags are left alone
    assert NewTag.objects.filter(id=unique_system_tag.id).exists()
    assert NewTag.objects.filter(project_id=project.id, label="user tag").count() == 2
