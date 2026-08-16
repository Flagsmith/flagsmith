"""https://docs.flagsmith.com/managing-flags/updating-flags"""

import pytest
from pytest_django.fixtures import DjangoAssertNumQueries

from environments.models import Environment
from features.future.services import delete_segment_override, update_flag
from features.future.types import UpdateFlagRequest
from features.models import Feature
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser

# Writing one segment override reads and writes the flag as a whole, so these counts
# hold however many overrides the flag has. They cover environments on v1 versioning
# only: on v2, a write clones the flag's every feature state into a new version, so
# its cost grows with the number of overrides no matter what this module does.
UPDATE_FLAG_QUERIES = 21
DELETE_SEGMENT_OVERRIDE_QUERIES = 35


@pytest.fixture()
def target_segment(project: Project) -> Segment:
    return Segment.objects.create(project=project, name="target")  # type: ignore[no-any-return]


@pytest.fixture()
def untouched_segments(
    request: pytest.FixtureRequest, project: Project
) -> list[Segment]:
    """Segments whose overrides the test under way writes nothing to."""
    return [
        Segment.objects.create(project=project, name=f"untouched-{index}")
        for index in range(request.param)
    ]


@pytest.fixture()
def flag_with_segment_overrides(
    admin_user: FFAdminUser,
    environment: Environment,
    feature: Feature,
    target_segment: Segment,
    untouched_segments: list[Segment],
) -> None:
    update_flag(
        environment=environment,
        feature=feature,
        changes=UpdateFlagRequest(
            {
                "segment_overrides": [
                    {"segment": {"id": segment.id}, "priority": priority}
                    for priority, segment in enumerate(
                        [target_segment, *untouched_segments]
                    )
                ],
            }
        ),
        replace=False,
        author=admin_user,
    )


@pytest.mark.parametrize("untouched_segments", [1, 3], indirect=True)
def test_update_flag__segment_overrides_untouched__queries_do_not_scale(
    admin_user: FFAdminUser,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
    feature: Feature,
    flag_with_segment_overrides: None,
    target_segment: Segment,
) -> None:
    # Given
    changes = UpdateFlagRequest(
        {"segment_overrides": [{"segment": {"id": target_segment.id}, "enabled": True}]}
    )

    # When / Then
    with django_assert_num_queries(UPDATE_FLAG_QUERIES):
        update_flag(
            environment=environment,
            feature=feature,
            changes=changes,
            replace=False,
            author=admin_user,
        )


@pytest.mark.parametrize("untouched_segments", [1, 3], indirect=True)
def test_delete_segment_override__segment_overrides_untouched__queries_do_not_scale(
    admin_user: FFAdminUser,
    django_assert_num_queries: DjangoAssertNumQueries,
    environment: Environment,
    feature: Feature,
    flag_with_segment_overrides: None,
    target_segment: Segment,
) -> None:
    # Given
    segment_id = target_segment.id

    # When / Then
    with django_assert_num_queries(DELETE_SEGMENT_OVERRIDE_QUERIES):
        delete_segment_override(
            environment=environment,
            feature=feature,
            segment_id=segment_id,
            author=admin_user,
        )
