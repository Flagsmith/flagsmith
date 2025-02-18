from typing import Type

import pytest
from django.contrib.auth.models import AbstractUser
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from pytest_mock import MockerFixture

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.dynatrace.dynatrace import EVENTS_API_URI, DynatraceWrapper
from projects.models import Project
from segments.models import Segment


def test_dynatrace_initialized_correctly():  # type: ignore[no-untyped-def]
    # Given
    api_key = "123key"
    base_url = "http://test.com"
    entity_selector = "type(APPLICATION),entityName(docs)"

    # When initialized
    dynatrace = DynatraceWrapper(
        base_url=base_url, api_key=api_key, entity_selector=entity_selector
    )

    # Then
    expected_url = f"{base_url}{EVENTS_API_URI}?api-token={api_key}"
    assert dynatrace.url == expected_url


@pytest.mark.parametrize(
    "related_object_type, related_object, expected_deployment_name",
    (
        (
            RelatedObjectType.FEATURE.name,
            lazy_fixture("feature"),
            "Flagsmith Deployment - Flag Changed: Test Feature1",
        ),
        (
            RelatedObjectType.FEATURE_STATE.name,
            lazy_fixture("feature_state"),
            "Flagsmith Deployment - Flag Changed: Test Feature1",
        ),
        (
            RelatedObjectType.SEGMENT.name,
            lazy_fixture("segment"),
            "Flagsmith Deployment - Segment Changed: segment",
        ),
    ),
)
def test_dynatrace_when_generate_event_data_with_correct_values_then_success(
    django_user_model: Type[AbstractUser],
    related_object_type: RelatedObjectType,
    related_object: Feature | Segment | FeatureState,
    expected_deployment_name: str,
    project: Project,
    environment: Environment,
    mocker: MockerFixture,
) -> None:
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")

    audit_log_record = AuditLog(
        log=log,
        author=author,
        environment=getattr(related_object, "environment", None),
        project=project,
        related_object_type=related_object_type,
        related_object_id=related_object.id,
    )

    mocker.patch(
        "integrations.dynatrace.dynatrace.get_audited_instance_from_audit_log_record",
        return_value=related_object,
    )

    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"

    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == (
        environment.name if hasattr(related_object, "environment") else "unknown"
    )
    assert (
        event_data["properties"]["dt.event.deployment.name"] == expected_deployment_name
    )


def test_dynatrace_when_generate_event_data_with_missing_author_then_success():  # type: ignore[no-untyped-def]
    # Given
    log = "some log data"

    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, environment=environment)

    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user system"
    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == environment.name


def test_dynatrace_when_generate_event_data_with_missing_environment_then_success(  # type: ignore[no-untyped-def]
    django_user_model, feature
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@example.com")

    audit_log_record = AuditLog(
        log=log,
        author=author,
        related_object_type=RelatedObjectType.FEATURE.name,
        related_object_id=feature.id,
    )

    dynatrace = DynatraceWrapper(
        base_url="http://test.com",
        api_key="123key",
        entity_selector="type(APPLICATION),entityName(docs)",
    )

    # When
    event_data = dynatrace.generate_event_data(audit_log_record=audit_log_record)

    # Then
    expected_event_text = f"{log} by user {author.email}"
    assert event_data["properties"]["event"] == expected_event_text
    assert event_data["properties"]["environment"] == "unknown"
