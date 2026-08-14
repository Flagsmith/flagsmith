import csv
import io
import json
from operator import attrgetter
from typing import Any
from unittest.mock import MagicMock

import pytest
from common.test_tools import SnapshotFixture
from django.conf import settings
from django.core import signing
from django.utils import timezone
from flag_engine.segments import constants as segment_constants
from pytest_mock import MockerFixture
from requests.exceptions import HTTPError, RequestException, Timeout

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import Feature, FeatureState
from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import (
    _serialize_variation_value,
    create_import_request,
    process_import_request,
)
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Condition, Segment, SegmentRule

# TODO: Delete alias as per https://github.com/Flagsmith/flagsmith/issues/7818
from segments.types import SegmentRule as SegmentRuleType
from users.models import FFAdminUser


def test_create_import_request__valid_project__returns_expected(
    ld_client_mock: MagicMock,
    ld_client_class_mock: MagicMock,
    project: Project,
    staff_user: FFAdminUser,
) -> None:
    # Given
    ld_project_key = "test-project-key"
    ld_token = "test-token"

    expected_salt = f"ld_import_{staff_user.id}"

    # When
    result = create_import_request(
        project=project,
        user=staff_user,
        ld_project_key=ld_project_key,
        ld_token=ld_token,
    )

    # Then
    ld_client_class_mock.assert_called_once_with(ld_token)
    ld_client_mock.get_project.assert_called_once_with(project_key=ld_project_key)
    ld_client_mock.get_flag_count.assert_called_once_with(project_key=ld_project_key)

    assert result.status == {
        "requested_environment_count": 2,
        "requested_flag_count": 9,
        "error_messages": [],
    }
    assert signing.loads(result.ld_token, salt=expected_salt) == ld_token
    assert result.ld_project_key == ld_project_key
    assert result.created_by == staff_user
    assert result.project == project


@pytest.mark.parametrize(
    "failing_ld_client_method_name",
    ["get_environments", "get_flags_by_envs", "get_flag_tags"],
)
@pytest.mark.parametrize(
    "exception, expected_error_message",
    [
        (
            HTTPError(response=MagicMock(status_code=503)),
            "HTTPError 503 when requesting /expected_path",
        ),
        (Timeout(), "Timeout when requesting /expected_path"),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_process_import_request__api_error__expected_status(
    ld_client_mock: MagicMock,
    ld_client_class_mock: MagicMock,
    failing_ld_client_method_name: str,
    exception: RequestException,
    expected_error_message: str,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given
    exception.request = MagicMock(path_url="/expected_path")
    getattr(ld_client_mock, failing_ld_client_method_name).side_effect = exception

    # When
    with pytest.raises(type(exception)):
        process_import_request(import_request)

    # Then
    assert import_request.completed_at
    assert import_request.ld_token == ""
    assert import_request.status["result"] == "failure"
    assert import_request.status["error_messages"] == [expected_error_message]


@pytest.mark.django_db(transaction=True)
def test_process_import_request__write_error__persists_no_import_data(
    mocker: MockerFixture,
    project: Project,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given
    mocker.patch(
        "integrations.launch_darkly.services._create_features_from_ld",
        side_effect=RuntimeError(),
    )

    # When
    with pytest.raises(RuntimeError):
        process_import_request(import_request)

    # Then
    import_request.refresh_from_db()
    assert import_request.completed_at
    assert import_request.status["result"] == "failure"
    assert not Environment.objects.filter(project=project).exists()
    assert not Feature.objects.filter(project=project).exists()
    assert not Segment.objects.filter(project=project).exists()


@pytest.mark.django_db(transaction=True)
def test_process_import_request__success__expected_status(  # type: ignore[no-untyped-def]
    project: Project,
    import_request: LaunchDarklyImportRequest,
):
    # Given
    if settings.WORKFLOWS_LOGIC_INSTALLED:
        # Delete any default tags created by workflows logic
        project.tags.all().delete()  # pragma: no cover

    # When
    process_import_request(import_request)

    # Then
    # Import request is marked as completed successfully.
    assert import_request.completed_at
    assert import_request.ld_token == ""
    assert import_request.status["result"] == "success"

    # Environment names are correct.
    assert list(
        Environment.objects.filter(project=project).values_list("name", flat=True)
    ) == ["Test", "Production"]

    # Feature names are correct.
    assert list(
        Feature.objects.filter(project=project).values_list("name", flat=True)
    ) == [
        "flag1",
        "flag2_value",
        "flag3_multivalue",
        "flag4_multivalue",
        "flag5",
        "TEST_TARGETED_CONTEXT",
        "TEST_INDIVIDUAL_TARGET",
        "TEST_SEGMENT_TARGET",
        "TEST_COMBINED_TARGET",
    ]

    # Tags are created and set as expected.
    assert set(Tag.objects.filter(project=project).values_list("label", "color")) == {
        ("testtag", "#3d4db6"),
        ("testtag2", "#3d4db6"),
        ("Imported", "#3d4db6"),
    }
    assert set(
        Feature.objects.filter(project=project).values_list("name", "tags__label")
    ) == {
        ("flag1", "Imported"),
        ("flag2_value", "Imported"),
        ("flag3_multivalue", "Imported"),
        ("flag4_multivalue", "Imported"),
        ("flag5", "testtag"),
        ("flag5", "Imported"),
        ("flag5", "testtag2"),
        ("TEST_TARGETED_CONTEXT", "Imported"),
        ("TEST_INDIVIDUAL_TARGET", "Imported"),
        ("TEST_SEGMENT_TARGET", "Imported"),
        ("TEST_COMBINED_TARGET", "Imported"),
    }

    # Deprecated flags are archived.
    deprecated_feature = Feature.objects.get(project=project, name="flag1")
    assert deprecated_feature.is_archived is True

    # Standard feature states have expected values.
    boolean_standard_feature = Feature.objects.get(project=project, name="flag1")
    boolean_standard_feature_states_by_env_name = {
        fs.environment.name: fs
        for fs in FeatureState.objects.filter(feature=boolean_standard_feature)
    }
    boolean_standard_feature_states_by_env_name["Test"].enabled is True
    boolean_standard_feature_states_by_env_name["Production"].enabled is False

    string_standard_feature = Feature.objects.get(project=project, name="flag2_value")
    string_standard_feature_states_by_env_name = {
        fs.environment.name: fs
        for fs in FeatureState.objects.filter(feature=string_standard_feature)
    }
    assert string_standard_feature_states_by_env_name["Test"].enabled is True
    assert (
        string_standard_feature_states_by_env_name["Test"].get_feature_state_value()
        == "123123"
    )
    assert (
        string_standard_feature_states_by_env_name["Test"].feature_state_value.type
        == "unicode"
    )
    assert (
        string_standard_feature_states_by_env_name[
            "Test"
        ].feature_state_value.string_value
        == "123123"
    )
    assert string_standard_feature_states_by_env_name["Production"].enabled is False
    assert (
        string_standard_feature_states_by_env_name[
            "Production"
        ].get_feature_state_value()
        == ""
    )
    assert (
        string_standard_feature_states_by_env_name[
            "Production"
        ].feature_state_value.type
        == "unicode"
    )
    assert (
        string_standard_feature_states_by_env_name[
            "Production"
        ].feature_state_value.string_value
        == ""
    )

    # Multivariate feature states with percentage rollout have expected values.
    percentage_mv_feature = Feature.objects.get(
        project=project, name="flag4_multivalue"
    )
    percentage_mv_feature_states_by_env_name = {
        fs.environment.name: fs
        for fs in FeatureState.objects.filter(feature=percentage_mv_feature)
    }

    assert percentage_mv_feature_states_by_env_name["Test"].enabled is False

    # The `off` variation from LD's environment is imported as the control value.
    assert (
        percentage_mv_feature_states_by_env_name["Test"].get_feature_state_value()
        == "variation2"
    )
    assert set(
        percentage_mv_feature_states_by_env_name[
            "Test"
        ].multivariate_feature_state_values.values_list(
            "multivariate_feature_option__string_value",
            "percentage_allocation",
        )
    ) == {("variation1", 100), ("variation2", 0), ("variation3", 0)}

    assert percentage_mv_feature_states_by_env_name["Production"].enabled is True

    # The `off` variation from LD's environment is imported as the control value.
    assert (
        percentage_mv_feature_states_by_env_name["Production"].get_feature_state_value()
        == "variation3"
    )
    assert set(
        percentage_mv_feature_states_by_env_name[
            "Production"
        ].multivariate_feature_state_values.values_list(
            "multivariate_feature_option__string_value",
            "percentage_allocation",
        )
    ) == {("variation1", 24), ("variation2", 25), ("variation3", 51)}

    # Tags are imported correctly.
    tagged_feature = Feature.objects.get(project=project, name="flag5")
    [tag.label for tag in tagged_feature.tags.all()] == ["testtag", "testtag2"]


@pytest.mark.django_db(transaction=True)
def test_process_import_request__already_completed__does_not_reprocess(
    ld_client_class_mock: MagicMock,
    ld_client_mock: MagicMock,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given
    import_request.status["result"] = "success"
    import_request.completed_at = timezone.now()
    import_request.ld_token = ""
    import_request.save()
    ld_client_class_mock.reset_mock()

    # When
    process_import_request(import_request)

    # Then
    ld_client_class_mock.assert_not_called()
    ld_client_mock.get_environments.assert_not_called()


@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_segments__creates_segment_per_environment(
    project: Project,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given / When
    process_import_request(import_request)

    # Then
    segments = Segment.objects.filter(project=project, feature_id=None)

    assert set(segments.values_list("name", flat=True)) == {
        "User List (Override for test)",
        "User List (Override for production)",
        "Dynamic List (Override for test)",
        "Dynamic List (Override for production)",
        "Dynamic List 2 (Override for test)",
        "Dynamic List 2 (Override for production)",
    }


@pytest.mark.parametrize(
    "segment_name, expected_rules_data",
    [
        pytest.param(
            "Dynamic List (Override for test)",
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "email",
                                    "operator": segment_constants.REGEX,
                                    "value": ".*@gmail\\.com",
                                    "description": None,
                                }
                            ],
                        }
                    ],
                }
            ],
            id="targeting-rules-only",
        ),
        pytest.param(
            "Dynamic List 2 (Override for production)",
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "p1",
                                    "operator": segment_constants.IN,
                                    "value": "1,2",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "p2",
                                    "operator": segment_constants.GREATER_THAN,
                                    "value": "1.0.0:semver",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "p3",
                                    "operator": segment_constants.REGEX,
                                    "value": "foo[0-9]{0,1}",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.ANY_RULE,  # included users
                            "conditions": [
                                {
                                    "property": "key",
                                    "operator": segment_constants.IN,
                                    "value": "foo",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.NONE_RULE,  # excluded users
                            "conditions": [
                                {
                                    "property": "key",
                                    "operator": segment_constants.IN,
                                    "value": "bar",
                                    "description": None,
                                }
                            ],
                        },
                    ],
                }
            ],
            id="targeting-rules-and-user-lists",
        ),
        pytest.param(
            "User List (Override for test)",
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [
                        {
                            "type": SegmentRule.ANY_RULE,  # included users
                            "conditions": [
                                {
                                    "property": "key",
                                    "operator": segment_constants.IN,
                                    "value": "user-102,user-101",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.NONE_RULE,  # excluded users
                            "conditions": [
                                {
                                    "property": "key",
                                    "operator": segment_constants.IN,
                                    "value": "user-103",
                                    "description": None,
                                }
                            ],
                        },
                    ],
                }
            ],
            id="user-lists-only",
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_segments__imports_correctly(
    project: Project,
    import_request: LaunchDarklyImportRequest,
    segment_name: str,
    expected_rules_data: list[SegmentRuleType],
) -> None:
    # Given / When
    process_import_request(import_request)

    # Then
    segment = Segment.objects.get(name=segment_name, project=project)
    assert segment.rules_data == expected_rules_data


@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_segments__creates_identities_with_key_traits(
    project: Project,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given / When
    process_import_request(import_request)

    # Then
    assert set(
        Identity.objects.filter(environment__project=project).values_list(
            "identifier",
            "identity_traits__trait_key",
            "identity_traits__string_value",
        )
    ) == {
        (identifier, "key", identifier)
        for identifier in (
            "bar",
            "foo",
            "user1",
            "user2",
            "user-101",
            "user-102",
            "user-103",
            "user-1005",
            "user-10006",
        )
    }


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_segments__imports_correctly_x_replaced_above(  # type: ignore[no-untyped-def]
    project: Project,
    import_request: LaunchDarklyImportRequest,
):
    # Given / When
    process_import_request(import_request)

    # Then
    segments = Segment.objects.filter(project=project, feature_id=None)

    assert set(segments.values_list("name", flat=True)) == {
        # Segments
        "User List (Override for test)",
        "User List (Override for production)",
        "Dynamic List (Override for test)",
        "Dynamic List (Override for production)",
        "Dynamic List 2 (Override for test)",
        "Dynamic List 2 (Override for production)",
    }

    # Tests for "Dynamic List (Override for test)"
    dynamic_list_test_segment = Segment.objects.get(
        name="Dynamic List (Override for test)"
    )
    dynamic_list_test_segment_rule = SegmentRule.objects.get(
        segment=dynamic_list_test_segment
    )
    # Parents are always "ALL" rules.
    assert dynamic_list_test_segment_rule.type == SegmentRule.ALL_RULE

    dynamic_list_test_segment_subrules = SegmentRule.objects.filter(
        rule=dynamic_list_test_segment_rule
    )
    assert dynamic_list_test_segment_subrules.count() == 1
    # UI needs to have subrules as `ANY_RULE` to display properly.
    assert list(dynamic_list_test_segment_subrules)[0].type == SegmentRule.ANY_RULE

    dynamic_list_test_segment_subrule_conditions = Condition.objects.filter(
        rule=dynamic_list_test_segment_subrules[0]
    )
    assert set(
        dynamic_list_test_segment_subrule_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("email", segment_constants.REGEX, ".*@gmail\\.com"),
    }

    # Tests for "Dynamic List 2 (Override for production)"
    dynamic_list_2_production_segment = Segment.objects.get(
        name="Dynamic List 2 (Override for production)"
    )
    dynamic_list_2_production_segment_rule = SegmentRule.objects.get(
        segment=dynamic_list_2_production_segment
    )
    # Parents are always "ALL" rules.
    assert dynamic_list_2_production_segment_rule.type == SegmentRule.ALL_RULE

    dynamic_list_2_production_segment_subrules = SegmentRule.objects.filter(
        rule=dynamic_list_2_production_segment_rule
    )
    assert dynamic_list_2_production_segment_subrules.count() == 5
    # UI needs to have subrules as `ANY_RULE` to display properly.
    assert (
        list(dynamic_list_2_production_segment_subrules)[0].type == SegmentRule.ANY_RULE
    )
    assert (
        list(dynamic_list_2_production_segment_subrules)[1].type == SegmentRule.ANY_RULE
    )
    assert (
        list(dynamic_list_2_production_segment_subrules)[2].type == SegmentRule.ANY_RULE
    )

    dynamic_list_2_production_segment_subrule_0_conditions = Condition.objects.filter(
        rule=dynamic_list_2_production_segment_subrules[0]
    )

    assert set(
        dynamic_list_2_production_segment_subrule_0_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("p1", segment_constants.IN, "1,2"),
    }

    dynamic_list_2_production_segment_subrule_1_conditions = Condition.objects.filter(
        rule=dynamic_list_2_production_segment_subrules[1]
    )
    assert set(
        dynamic_list_2_production_segment_subrule_1_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("p2", segment_constants.GREATER_THAN, "1.0.0:semver"),
    }

    dynamic_list_2_production_segment_subrule_2_conditions = Condition.objects.filter(
        rule=dynamic_list_2_production_segment_subrules[2]
    )
    assert set(
        dynamic_list_2_production_segment_subrule_2_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("p3", segment_constants.REGEX, "foo[0-9]{0,1}"),
    }

    # Include individual users
    assert (
        list(dynamic_list_2_production_segment_subrules)[3].type == SegmentRule.ANY_RULE
    )
    dynamic_list_2_production_segment_subrule_3_conditions = Condition.objects.filter(
        rule=dynamic_list_2_production_segment_subrules[3]
    )
    assert set(
        dynamic_list_2_production_segment_subrule_3_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("key", segment_constants.IN, "foo"),
    }

    # Exclude individual users
    assert (
        list(dynamic_list_2_production_segment_subrules)[4].type
        == SegmentRule.NONE_RULE
    )
    dynamic_list_2_production_segment_subrule_4_conditions = Condition.objects.filter(
        rule=dynamic_list_2_production_segment_subrules[4]
    )
    assert set(
        dynamic_list_2_production_segment_subrule_4_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("key", segment_constants.IN, "bar"),
    }

    # User list segments
    user_list_test_segment = Segment.objects.get(name="User List (Override for test)")
    user_list_test_segment_rule = SegmentRule.objects.get(
        segment=user_list_test_segment
    )
    # Parents are always "ALL" rules.
    assert user_list_test_segment_rule.type == SegmentRule.ALL_RULE

    user_list_test_segment_subrules = SegmentRule.objects.filter(
        rule=user_list_test_segment_rule
    )
    assert user_list_test_segment_subrules.count() == 2
    assert list(user_list_test_segment_subrules)[0].type == SegmentRule.ANY_RULE
    user_list_test_segment_subrule_0_conditions = Condition.objects.filter(
        rule=user_list_test_segment_subrules[0]
    )
    assert set(
        user_list_test_segment_subrule_0_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("key", segment_constants.IN, "user-102,user-101"),
    }

    assert list(user_list_test_segment_subrules)[1].type == SegmentRule.NONE_RULE
    user_list_test_segment_subrule_1_conditions = Condition.objects.filter(
        rule=user_list_test_segment_subrules[1]
    )
    assert set(
        user_list_test_segment_subrule_1_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("key", segment_constants.IN, "user-103"),
    }

    identifies_created = set(
        Identity.objects.filter(environment__project=project).values_list(
            "identifier", flat=True
        )
    )

    assert identifies_created == {
        "bar",
        "user-10006",
        "user-102",
        "user2",
        "user-103",
        "user-101",
        "foo",
        "user1",
        "user-1005",
    }

    # Each identity should have a trait called "key"
    for identity in list(Identity.objects.filter(environment__project=project).all()):
        trait_value = Trait.objects.get(  # type: ignore[no-untyped-call]
            identity=identity, trait_key="key"
        ).get_trait_value()
        assert trait_value == identity.identifier


@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_rules__creates_feature_specific_segments(
    project: Project,
    import_request: LaunchDarklyImportRequest,
) -> None:
    # Given / When
    process_import_request(import_request)

    # Then
    segments = Segment.objects.filter(project=project).exclude(feature_id=None)

    assert set(segments.values_list("name", flat=True)) == {
        # Feature Segments
        "Regular And",
        "Reverted And",
        "Just Not",
        # Feature Segments without descriptions
        "imported-56725db6-3d2a-4ed6-a2a1-60ef94ac62d5",
        "imported-a132f4aa-ad51-43c6-8d03-f18d6a5b205d",
        "imported-c034ec70-fcb3-4c15-9bea-b9fa0b341b4f",
        # Individual targeting rules converted as custom segments
        "individual-targeting-variation-0",
        "individual-targeting-variation-1",
        "individual-targeting-variation-2",
    }


@pytest.mark.parametrize(
    "segment_name, expected_rules_data",
    [
        pytest.param(
            "Regular And",
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "p1",
                                    "operator": segment_constants.LESS_THAN_INCLUSIVE,
                                    "value": "5",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "p2",
                                    "operator": segment_constants.GREATER_THAN,
                                    "value": "1",
                                    "description": None,
                                }
                            ],
                        },
                    ],
                }
            ],
            id="plain-clauses-only",
        ),
        pytest.param(
            "Reverted And",
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [
                        {
                            "type": SegmentRule.ANY_RULE,
                            "conditions": [
                                {
                                    "property": "p1",
                                    "operator": segment_constants.REGEX,
                                    "value": ".*bar",
                                    "description": None,
                                }
                            ],
                        },
                        {
                            "type": SegmentRule.NONE_RULE,  # negated clauses pool here
                            "conditions": [
                                {
                                    "property": "p2",
                                    "operator": segment_constants.CONTAINS,
                                    "value": "forbidden",
                                    "description": None,
                                },
                                {
                                    "property": "p2",
                                    "operator": segment_constants.CONTAINS,
                                    "value": "words",
                                    "description": None,
                                },
                            ],
                        },
                    ],
                }
            ],
            id="plain-and-negated-clauses",
        ),
        pytest.param(
            "Just Not",
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [
                        {
                            "type": SegmentRule.NONE_RULE,
                            "conditions": [
                                {
                                    "property": "p1",
                                    "operator": segment_constants.IN,
                                    "value": "this,that",
                                    "description": None,
                                }
                            ],
                        },
                    ],
                }
            ],
            id="negated-clauses-only",
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_rules__imports_correctly(
    project: Project,
    import_request: LaunchDarklyImportRequest,
    segment_name: str,
    expected_rules_data: list[SegmentRuleType],
) -> None:
    # Given / When
    process_import_request(import_request)

    # Then
    segment = Segment.objects.get(name=segment_name, project=project)
    assert segment.rules_data == expected_rules_data


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
@pytest.mark.django_db(transaction=True)
def test_process_import_request__valid_rules__imports_correctly_x_replaced_above(  # type: ignore[no-untyped-def]
    project: Project,
    import_request: LaunchDarklyImportRequest,
):
    # Given / When
    process_import_request(import_request)

    # Then
    segments = Segment.objects.filter(project=project).exclude(feature_id=None)

    assert set(segments.values_list("name", flat=True)) == {
        # Feature Segments
        "Regular And",
        "Reverted And",
        "Just Not",
        # Feature Segments without descriptions
        "imported-56725db6-3d2a-4ed6-a2a1-60ef94ac62d5",
        "imported-a132f4aa-ad51-43c6-8d03-f18d6a5b205d",
        "imported-c034ec70-fcb3-4c15-9bea-b9fa0b341b4f",
        # Individual targeting rules converted as custom segments
        "individual-targeting-variation-0",
        "individual-targeting-variation-1",
        "individual-targeting-variation-2",
    }

    # Tests for "Regular And"

    and_rule = SegmentRule.objects.get(segment__name="Regular And")
    # Parents are always "ALL" rules.
    assert and_rule.type == SegmentRule.ALL_RULE

    and_subrules = SegmentRule.objects.filter(rule=and_rule)
    assert and_subrules.count() == 2
    # UI needs to have subrules as `ANY_RULE` to display properly.
    assert list(and_subrules)[0].type == SegmentRule.ANY_RULE
    assert list(and_subrules)[1].type == SegmentRule.ANY_RULE

    and_subconditions = Condition.objects.filter(rule__in=and_subrules)
    assert and_subconditions.count() == 2
    assert set(and_subconditions.values_list("property", "operator", "value")) == {
        ("p1", segment_constants.LESS_THAN_INCLUSIVE, "5"),
        ("p2", segment_constants.GREATER_THAN, "1"),
    }

    # Tests for "Reverted And"

    reverted_and_rule = SegmentRule.objects.get(segment__name="Reverted And")
    # Parents are always "ALL" rules.
    assert reverted_and_rule.type == SegmentRule.ALL_RULE

    reverted_and_subrules = SegmentRule.objects.filter(rule=reverted_and_rule).all()
    assert reverted_and_subrules.count() == 2
    assert list(reverted_and_subrules)[0].type == SegmentRule.ANY_RULE
    assert list(reverted_and_subrules)[1].type == SegmentRule.NONE_RULE

    reverted_and_any_subrule_conditions = Condition.objects.filter(
        rule=reverted_and_subrules[0]
    )
    assert reverted_and_any_subrule_conditions.count() == 1
    assert set(
        reverted_and_any_subrule_conditions.values_list("property", "operator", "value")
    ) == {
        ("p1", segment_constants.REGEX, ".*bar"),
    }

    reverted_and_none_subrule_conditions = Condition.objects.filter(
        rule=reverted_and_subrules[1]
    )
    assert reverted_and_none_subrule_conditions.count() == 2
    assert set(
        reverted_and_none_subrule_conditions.values_list(
            "property", "operator", "value"
        )
    ) == {
        ("p2", segment_constants.CONTAINS, "forbidden"),
        ("p2", segment_constants.CONTAINS, "words"),
    }

    # Tests for "Just Not
    just_not_rule = SegmentRule.objects.get(segment__name="Just Not")
    # Parents are always "ALL" rules.
    assert just_not_rule.type == SegmentRule.ALL_RULE

    just_not_subrules = SegmentRule.objects.filter(rule=just_not_rule).all()
    assert just_not_subrules.count() == 1
    assert list(just_not_subrules)[0].type == SegmentRule.NONE_RULE

    just_not_subrule_conditions = Condition.objects.filter(rule=just_not_subrules[0])
    assert just_not_subrule_conditions.count() == 1
    assert set(
        just_not_subrule_conditions.values_list("property", "operator", "value")
    ) == {
        ("p1", segment_constants.IN, "this,that"),
    }


@pytest.mark.parametrize(
    "ld_segment_data, expected_rules_data, expected_error_message",
    [
        pytest.param(
            {
                "rules": [
                    {
                        "clauses": [
                            {
                                "attribute": "p1",
                                "op": "arcaneOp",
                                "values": ["x"],
                                "negate": False,
                            }
                        ]
                    }
                ]
            },
            [{"type": SegmentRule.ALL_RULE, "conditions": [], "rules": []}],
            "Can't map launch darkly operator: arcaneOp"
            " skipping for segment: Unsupported (Override for test)",
            id="unsupported-operator",
        ),
        pytest.param(
            {
                "rules": [
                    {
                        "clauses": [
                            {
                                "attribute": "p1",
                                "op": "contains",
                                "values": [
                                    "x" * (settings.SEGMENT_CONDITION_VALUE_LIMIT + 1)
                                ],
                                "negate": False,
                            }
                        ]
                    }
                ]
            },
            [
                {
                    "type": SegmentRule.ALL_RULE,
                    "conditions": [],
                    "rules": [{"type": SegmentRule.ANY_RULE, "conditions": []}],
                }
            ],
            f"Segment condition value 'xxxxx...xxxxx' for property 'p1' exceeds the"
            f" limit of {settings.SEGMENT_CONDITION_VALUE_LIMIT} characters,"
            f" skipping for segment 'Unsupported (Override for test)'",
            id="condition-value-over-limit",
        ),
        pytest.param(
            {"included": ["y" * (settings.SEGMENT_CONDITION_VALUE_LIMIT + 1)]},
            [{"type": SegmentRule.ALL_RULE, "conditions": [], "rules": []}],
            f"Targeting key 'yyyyy...yyyyy' exceeds the limit of"
            f" {settings.SEGMENT_CONDITION_VALUE_LIMIT} characters, "
            f"skipping for segment 'Unsupported (Override for test)'",
            id="targeting-key-over-limit",
        ),
    ],
)
@pytest.mark.django_db(transaction=True)
def test_process_import_request__unsupported_segment_data__skips_and_logs_error(
    project: Project,
    ld_client_class_mock: MagicMock,
    import_request: LaunchDarklyImportRequest,
    ld_segment_data: dict[str, Any],
    expected_rules_data: list[SegmentRuleType],
    expected_error_message: str,
) -> None:
    # Given
    ld_client_class_mock.return_value.get_segments.return_value = [
        {
            "name": "Unsupported",
            "key": "unsupported",
            "deleted": False,
            "included": [],
            "excluded": [],
            "includedContexts": [],
            "excludedContexts": [],
            "rules": [],
            **ld_segment_data,
        }
    ]

    # When
    process_import_request(import_request)

    # Then
    segment = Segment.objects.get(
        name="Unsupported (Override for test)", project=project
    )
    assert segment.rules_data == expected_rules_data
    assert expected_error_message in import_request.status["error_messages"]


@pytest.mark.django_db(transaction=True)
def test_process_import_request__large_segments__correctly_imported(
    request: pytest.FixtureRequest,
    ld_client_class_mock: MagicMock,
    import_request: LaunchDarklyImportRequest,
    snapshot: SnapshotFixture,
) -> None:
    # Given
    expected_status_snapshot = snapshot(
        "test_process_import_request__large_segments__correctly_imported__import_request_status.json"
    )
    expected_rules_data_snapshot = snapshot(
        "test_process_import_request__large_segments__correctly_imported__rules_data.json"
    )
    expected_segment_names = [
        "Large Dynamic List (Override for test)",
        "Large Dynamic List (Override for production)",
        "Large User List (Override for test)",
        "Large User List (Override for production)",
    ]
    large_segments_response_path = (
        request.path.parent / "client_responses/get_segments__large_segments.json"
    )
    ld_client_class_mock.return_value.get_segments.return_value = json.loads(
        large_segments_response_path.read_text()
    )

    # When
    process_import_request(import_request)

    # Then
    status_json = json.dumps(import_request.status, indent=2, sort_keys=True)
    assert status_json == expected_status_snapshot

    segments = sorted(
        Segment.objects.filter(
            project=import_request.project, name__in=expected_segment_names
        ),
        key=attrgetter("name"),
    )
    rules_data_json = json.dumps(
        {segment.name: segment.rules_data for segment in segments}, indent=2
    )
    assert rules_data_json == expected_rules_data_snapshot


# TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
@pytest.mark.django_db(transaction=True)
def test_process_import_request__large_segments__correctly_imported_x_replaced_above(
    request: pytest.FixtureRequest,
    ld_client_class_mock: MagicMock,
    import_request: LaunchDarklyImportRequest,
    snapshot: SnapshotFixture,
) -> None:
    # Given
    expected_import_request_status_snapshot, expected_condition_data_snapshot = (
        snapshot(
            "test_process_import_request__large_segments__correctly_imported__import_request_status.json"
        ),
        snapshot(
            "test_process_import_request__large_segments__correctly_imported__condition_data.csv"
        ),
    )
    expected_segment_names = [
        "Large Dynamic List (Override for test)",
        "Large Dynamic List (Override for production)",
        "Large User List (Override for test)",
        "Large User List (Override for production)",
    ]
    ld_client_class_mock.return_value.get_segments.return_value = json.loads(
        (
            request.path.parent / "client_responses/get_segments__large_segments.json"
        ).read_text()
    )

    # When
    process_import_request(import_request)

    # Then
    assert (
        json.dumps(
            import_request.status,
            indent=2,
            sort_keys=True,
        )
        == expected_import_request_status_snapshot
    )
    buf = io.StringIO()
    csv_writer = csv.writer(buf, dialect="unix", lineterminator="\n")
    csv_writer.writerow(
        ["Segment Name", "Property", "Operator", "Value", "Rule Type"],
    )
    csv_writer.writerows(
        [
            (segment.name, *condition_values)
            for segment in sorted(
                Segment.objects.filter(
                    project=import_request.project,
                    name__in=expected_segment_names,
                ),
                key=attrgetter("name"),
            )
            for condition_values in sorted(
                Condition.objects.filter(
                    rule__rule__segment__name=segment.name
                ).values_list("property", "operator", "value", "rule__type"),
            )
        ]
    )
    assert buf.getvalue() == expected_condition_data_snapshot


@pytest.mark.parametrize(
    "value, expected",
    [
        (
            {"enabled": True, "description": "test"},
            '{"enabled": true, "description": "test"}',
        ),
        ([1, 2, 3], "[1, 2, 3]"),
        ("string_value", "string_value"),
        (123, "123"),
        (True, "True"),
    ],
)
def test_serialize_variation_value__various_types__returns_expected(
    value: object,
    expected: str,
) -> None:
    # Given / When
    result = _serialize_variation_value(value)

    # Then
    assert result == expected


@pytest.mark.django_db(transaction=True)
def test_process_import_request__import__enqueues_membership_refresh(
    import_request: LaunchDarklyImportRequest,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given
    enqueue_membership_refresh_mock = mocker.patch(
        "integrations.launch_darkly.services.enqueue_membership_refresh"
    )

    # When
    process_import_request(import_request)

    # Then
    enqueue_membership_refresh_mock.assert_called_once_with(project)
