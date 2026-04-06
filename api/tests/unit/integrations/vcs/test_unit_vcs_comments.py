import pytest

from integrations.vcs.comments import generate_body_comment

pytestmark = pytest.mark.django_db


def test_generate_body_comment__flag_deleted__returns_deleted_text() -> None:
    # Given
    # When
    result = generate_body_comment(
        name="my_flag",
        event_type="FLAG_DELETED",
        feature_id=1,
        feature_states=[],
        unlinked_feature_text="unlinked %s",
    )

    # Then
    assert "my_flag" in result
    assert "deleted" in result.lower()


def test_generate_body_comment__resource_removed__returns_unlinked_text() -> None:
    # Given
    # When
    result = generate_body_comment(
        name="my_flag",
        event_type="FEATURE_EXTERNAL_RESOURCE_REMOVED",
        feature_id=1,
        feature_states=[],
        unlinked_feature_text="**The flag `%s` was unlinked**",
    )

    # Then
    assert result == "**The flag `my_flag` was unlinked**"


def test_generate_body_comment__flag_updated__returns_table() -> None:
    # Given
    feature_states = [
        {
            "environment_name": "Production",
            "enabled": True,
            "feature_state_value": "on",
            "last_updated": "2026-01-01",
            "environment_api_key": "api-key-123",
        },
    ]

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type="FLAG_UPDATED",
        feature_id=1,
        feature_states=feature_states,
        unlinked_feature_text="unlinked %s",
        project_id=1,
    )

    # Then
    assert "my_flag" in result
    assert "Production" in result
    assert "Enabled" in result
    assert "`on`" in result


def test_generate_body_comment__segment_override_deleted__returns_segment_text() -> None:
    # Given
    # When
    result = generate_body_comment(
        name="my_flag",
        event_type="SEGMENT_OVERRIDE_DELETED",
        feature_id=1,
        feature_states=[],
        unlinked_feature_text="unlinked %s",
        segment_name="beta_users",
    )

    # Then
    assert "beta_users" in result
    assert "my_flag" in result


def test_generate_body_comment__resource_added__returns_linked_table() -> None:
    # Given
    feature_states = [
        {
            "environment_name": "Staging",
            "enabled": False,
            "feature_state_value": None,
            "last_updated": "2026-01-01",
            "environment_api_key": "api-key-456",
        },
    ]

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type="FEATURE_EXTERNAL_RESOURCE_ADDED",
        feature_id=1,
        feature_states=feature_states,
        unlinked_feature_text="unlinked %s",
        project_id=1,
    )

    # Then
    assert "Flagsmith feature linked" in result
    assert "Staging" in result
    assert "Disabled" in result


def test_generate_body_comment__with_segment_states__renders_segment_header() -> None:
    # Given
    feature_states = [
        {
            "environment_name": "Production",
            "enabled": True,
            "feature_state_value": "v1",
            "last_updated": "2026-01-01",
            "environment_api_key": "api-key-123",
            "segment_name": "beta_users",
        },
    ]

    # When
    result = generate_body_comment(
        name="my_flag",
        event_type="FLAG_UPDATED",
        feature_id=1,
        feature_states=feature_states,
        unlinked_feature_text="unlinked %s",
        project_id=1,
    )

    # Then
    assert "beta_users" in result
    assert "Segment" in result
