"""
def test_environment_admin_rebuild_environments(environment, mocker):
    # GIVEN
    mocked_rebuild_environment_document = mocker.patch(
        "environments.admin.rebuild_environment_document"
    )
    environment_admin = EnvironmentAdmin(Environment, AdminSite())
    # WHEN
    environment_admin.rebuild_environments(
        request=mocker.MagicMock(), queryset=Environment.objects.all()
    )
    # THEN
    mocked_rebuild_environment_document.delay.assert_called_once_with(
        args=(environment.id,)
    )
"""
import typing
from unittest.mock import MagicMock

from django.contrib.admin import AdminSite

from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from projects.admin import ProjectAdmin
from projects.models import Project
from segments.models import EQUAL, Condition, Segment, SegmentRule

if typing.TYPE_CHECKING:
    from organisations.models import Organisation


def test_project_admin_delete_all_segments(organisation: "Organisation"):
    # Given
    project_1 = Project.objects.create(name="project_1", organisation=organisation)
    project_2 = Project.objects.create(name="project_2", organisation=organisation)

    for project in (project_1, project_2):
        segment = Segment.objects.create(name="segment", project=project)
        parent_rule = SegmentRule.objects.create(
            segment=segment, type=SegmentRule.ALL_RULE
        )
        child_rule = SegmentRule.objects.create(
            rule=parent_rule, type=SegmentRule.ANY_RULE
        )
        Condition.objects.create(
            rule=child_rule, property="foo", operator=EQUAL, value="bar"
        )

        environment = Environment.objects.create(name="test", project=project)
        feature = Feature.objects.create(name="test", project=project)

        feature_segment = FeatureSegment.objects.create(
            feature=feature, environment=environment, segment=segment
        )
        FeatureState.objects.create(
            feature=feature, environment=environment, feature_segment=feature_segment
        )

    project_admin = ProjectAdmin(Project, AdminSite())

    # When
    project_admin.delete_all_segments(
        request=MagicMock(), queryset=Project.objects.filter(id=project_1.id)
    )

    # Then
    assert not project_1.segments.exists()
    assert not FeatureState.objects.filter(
        feature=feature, environment__project=project_1, feature_segment__isnull=False
    ).exists()

    assert project_2.segments.exists()
    assert FeatureState.objects.filter(
        feature=feature, environment__project=project_2, feature_segment__isnull=False
    ).exists()
