import typing

import pytest
from django.contrib.contenttypes.models import ContentType

from cohorts.models import Cohort, CohortSourceType, CohortSyncKey
from environments.models import Environment
from metadata.models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from projects.models import Project
from segments.models import Segment


@pytest.fixture()
def cohort(environment: Environment, segment: Segment) -> Cohort:
    cohort: Cohort = Cohort.objects.create(environment=environment, segment=segment)
    return cohort


@pytest.fixture()
def required_segment_metadata_field_for_dynamo_project(
    a_metadata_field: MetadataField,
    dynamo_enabled_project: Project,
) -> MetadataModelField:
    model_field: MetadataModelField = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=ContentType.objects.get_for_model(Segment),
    )
    MetadataModelFieldRequirement.objects.create(
        content_type=ContentType.objects.get_for_model(Project),
        object_id=dynamo_enabled_project.id,
        model_field=model_field,
    )
    return model_field


@pytest.fixture()
def cohort_sync_key(
    dynamo_enabled_project_environment_one: Environment,
) -> typing.Tuple[CohortSyncKey, str]:
    return typing.cast(
        typing.Tuple[CohortSyncKey, str],
        CohortSyncKey.objects.create_key(
            name="test key", environment=dynamo_enabled_project_environment_one
        ),
    )


@pytest.fixture()
def amplitude_cohort(
    dynamo_enabled_project: Project,
    dynamo_enabled_project_environment_one: Environment,
) -> Cohort:
    segment = Segment.objects.create(
        name="amplitude segment", project=dynamo_enabled_project
    )
    cohort: Cohort = Cohort.objects.create(
        environment=dynamo_enabled_project_environment_one,
        segment=segment,
        source_type=CohortSourceType.AMPLITUDE,
    )
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
