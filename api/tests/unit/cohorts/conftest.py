import pytest

from cohorts.models import Cohort
from environments.models import Environment
from projects.models import Project
from segments.models import Segment


@pytest.fixture()
def cohort(environment: Environment, segment: Segment) -> Cohort:
    cohort: Cohort = Cohort.objects.create(environment=environment, segment=segment)
    return cohort


@pytest.fixture()
def edge_cohort(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
) -> Cohort:
    segment = Segment.objects.create(
        name="edge segment", project=dynamo_enabled_project
    )
    cohort: Cohort = Cohort.objects.create(
        environment=dynamo_enabled_project_environment_one, segment=segment
    )
    return cohort
