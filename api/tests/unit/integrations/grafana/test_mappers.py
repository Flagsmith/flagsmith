from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from audit.models import AuditLog
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from integrations.grafana.mappers import (
    map_audit_log_record_to_grafana_annotation,
)
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment
from users.models import FFAdminUser


@pytest.fixture
def audit_log_record(
    superuser: FFAdminUser,
    project: Project,
) -> AuditLog:
    return AuditLog.objects.create(
        created_date=datetime(2024, 6, 24, 9, 9, 47, 325132, tzinfo=timezone.utc),
        log="Test event",
        author=superuser,
        project=project,
    )


@pytest.fixture
def tagged_feature(
    feature: Feature,
    tag_one: Tag,
    tag_two: Tag,
) -> Feature:
    feature.tags.add(tag_one, tag_two)
    feature.save()
    return feature


def test_map_audit_log_record_to_grafana_annotation__feature__return_expected(
    mocker: MockerFixture,
    tagged_feature: Feature,
    audit_log_record: AuditLog,
) -> None:
    # Given
    mocker.patch(
        "integrations.grafana.mappers.get_audited_instance_from_audit_log_record",
        return_value=tagged_feature,
    )

    # When
    annotation = map_audit_log_record_to_grafana_annotation(audit_log_record)

    # Then
    assert annotation == {
        "tags": [
            "flagsmith",
            "project:Test Project",
            "environment:unknown",
            "by:superuser@example.com",
            "feature:Test Feature1",
            "Test Tag",
            "Test Tag2",
        ],
        "text": "Test event",
        "time": 1719220187325,
        "timeEnd": 1719220187325,
    }


def test_map_audit_log_record_to_grafana_annotation__feature_state__return_expected(
    mocker: MockerFixture,
    tagged_feature: Feature,
    environment: Environment,
    audit_log_record: AuditLog,
) -> None:
    # Given
    feature_state = FeatureState.objects.filter(
        environment=environment,
        feature=tagged_feature,
    ).first()
    mocker.patch(
        "integrations.grafana.mappers.get_audited_instance_from_audit_log_record",
        return_value=feature_state,
    )
    audit_log_record.environment = environment

    # When
    annotation = map_audit_log_record_to_grafana_annotation(audit_log_record)

    # Then
    assert annotation == {
        "tags": [
            "flagsmith",
            "project:Test Project",
            "environment:Test Environment",
            "by:superuser@example.com",
            "feature:Test Feature1",
            "flag:disabled",
            "Test Tag",
            "Test Tag2",
        ],
        "text": "Test event",
        "time": 1719220187325,
        "timeEnd": 1719220187325,
    }


def test_map_audit_log_record_to_grafana_annotation__feature_state_value__return_expected(
    mocker: MockerFixture,
    tagged_feature: Feature,
    environment: Environment,
    audit_log_record: AuditLog,
) -> None:
    # Given
    feature_state_value = (
        FeatureState.objects.filter(
            environment=environment,
            feature=tagged_feature,
        )
        .first()
        .feature_state_value
    )
    mocker.patch(
        "integrations.grafana.mappers.get_audited_instance_from_audit_log_record",
        return_value=feature_state_value,
    )
    audit_log_record.environment = environment

    # When
    annotation = map_audit_log_record_to_grafana_annotation(audit_log_record)

    # Then
    assert annotation == {
        "tags": [
            "flagsmith",
            "project:Test Project",
            "environment:Test Environment",
            "by:superuser@example.com",
            "feature:Test Feature1",
            "Test Tag",
            "Test Tag2",
        ],
        "text": "Test event",
        "time": 1719220187325,
        "timeEnd": 1719220187325,
    }


def test_map_audit_log_record_to_grafana_annotation__segment__return_expected(
    mocker: MockerFixture,
    segment: Segment,
    audit_log_record: AuditLog,
) -> None:
    # Given
    mocker.patch(
        "integrations.grafana.mappers.get_audited_instance_from_audit_log_record",
        return_value=segment,
    )

    # When
    annotation = map_audit_log_record_to_grafana_annotation(audit_log_record)

    # Then
    assert annotation == {
        "tags": [
            "flagsmith",
            "project:Test Project",
            "environment:unknown",
            "by:superuser@example.com",
            "segment:segment",
        ],
        "text": "Test event",
        "time": 1719220187325,
        "timeEnd": 1719220187325,
    }


def test_map_audit_log_record_to_grafana_annotation__feature_segment__return_expected(
    mocker: MockerFixture,
    tagged_feature: Feature,
    feature_segment: FeatureSegment,
    audit_log_record: AuditLog,
) -> None:
    # Given
    mocker.patch(
        "integrations.grafana.mappers.get_audited_instance_from_audit_log_record",
        return_value=feature_segment,
    )

    # When
    annotation = map_audit_log_record_to_grafana_annotation(audit_log_record)

    # Then
    assert annotation == {
        "tags": [
            "flagsmith",
            "project:Test Project",
            "environment:unknown",
            "by:superuser@example.com",
            "feature:Test Feature1",
            "segment:segment",
            "Test Tag",
            "Test Tag2",
        ],
        "text": "Test event",
        "time": 1719220187325,
        "timeEnd": 1719220187325,
    }


@pytest.mark.django_db
def test_map_audit_log_record_to_grafana_annotation__generic__return_expected(
    mocker: MockerFixture,
    audit_log_record: AuditLog,
) -> None:
    # Given
    mocker.patch(
        "integrations.grafana.mappers.get_audited_instance_from_audit_log_record",
        return_value=None,
    )

    # When
    annotation = map_audit_log_record_to_grafana_annotation(audit_log_record)

    # Then
    assert annotation == {
        "tags": [
            "flagsmith",
            "project:Test Project",
            "environment:unknown",
            "by:superuser@example.com",
        ],
        "text": "Test event",
        "time": 1719220187325,
        "timeEnd": 1719220187325,
    }
