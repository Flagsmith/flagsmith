import pytest

from audit.constants import (
    RELEASE_PIPELINE_CREATED_MESSAGE,
    RELEASE_PIPELINE_DELETED_MESSAGE,
    RELEASE_PIPELINE_PUBLISHED_MESSAGE,
)
from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.release_pipelines.core.exceptions import InvalidPipelineStateError
from features.release_pipelines.core.models import (
    PipelineStage,
    ReleasePipeline,
)
from users.models import FFAdminUser


def test_release_pipeline_publish_creates_audit_log(
    release_pipeline: ReleasePipeline, admin_user: FFAdminUser
) -> None:
    # When
    release_pipeline.publish(admin_user)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=release_pipeline.id,
            related_object_type=RelatedObjectType.RELEASE_PIPELINE.name,
            project=release_pipeline.project,
            log=RELEASE_PIPELINE_PUBLISHED_MESSAGE % release_pipeline.name,
            author=admin_user,
        ).exists()
        is True
    )


def test_release_pipeline_publish_raises_error_if_pipeline_is_already_published(
    release_pipeline: ReleasePipeline, admin_user: FFAdminUser
) -> None:
    # Given - the pipeline is already published
    release_pipeline.publish(admin_user)

    # When / Then
    with pytest.raises(
        InvalidPipelineStateError, match="Pipeline is already published."
    ):
        release_pipeline.publish(admin_user)


def test_release_pipeline_get_first_stage_returns_none_if_pipeline_has_no_stages(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    first_stage = release_pipeline.get_first_stage()

    # Then
    assert first_stage is None


def test_release_pipeline_get_first_stage_returns_correct_stage(
    release_pipeline: ReleasePipeline, environment: Environment
) -> None:
    # Given
    for i in range(3):
        PipelineStage.objects.create(
            name=f"Stage {i}",
            pipeline=release_pipeline,
            environment=environment,
            order=i,
        )

    # When
    first_stage = release_pipeline.get_first_stage()

    # Then
    assert first_stage.order == 0  # type: ignore[union-attr]


def test_release_pipeline_get_last_stage_returns_none_if_pipeline_has_no_stages(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    last_stage = release_pipeline.get_last_stage()

    # Then
    assert last_stage is None


def test_release_pipeline_get_last_stage_returns_correct_stage(
    release_pipeline: ReleasePipeline, environment: Environment
) -> None:
    # Given
    for i in range(3):
        PipelineStage.objects.create(
            name=f"Stage {i}",
            pipeline=release_pipeline,
            environment=environment,
            order=i,
        )

    # When
    last_stage = release_pipeline.get_last_stage()

    # Then
    assert last_stage.order == 2  # type: ignore[union-attr]


def test_release_pipeline_get_next_stage(
    release_pipeline: ReleasePipeline, environment: Environment
) -> None:
    # Given
    stage1 = PipelineStage.objects.create(
        name="Stage 1",
        pipeline=release_pipeline,
        environment=environment,
        order=0,
    )
    stage2 = PipelineStage.objects.create(
        name="Stage 2",
        pipeline=release_pipeline,
        environment=environment,
        order=1,
    )
    stage3 = PipelineStage.objects.create(
        name="Stage 3",
        pipeline=release_pipeline,
        environment=environment,
        order=2,
    )

    # Then
    assert stage1.get_next_stage() == stage2
    assert stage2.get_next_stage() == stage3
    assert stage3.get_next_stage() is None


def test_release_pipeline_get_create_log_message(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    expected_message = RELEASE_PIPELINE_CREATED_MESSAGE % release_pipeline.name

    # Then
    assert release_pipeline.get_create_log_message(release_pipeline) == expected_message


def test_release_pipeline_get_delete_log_message(
    release_pipeline: ReleasePipeline,
) -> None:
    # When
    expected_message = RELEASE_PIPELINE_DELETED_MESSAGE % release_pipeline.name

    # Then
    assert release_pipeline.get_delete_log_message(release_pipeline) == expected_message
