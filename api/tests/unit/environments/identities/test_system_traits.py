from environments.dynamodb import DynamoIdentityWrapper
from environments.identities.models import Identity
from environments.identities.system_traits import (
    set_system_trait,
    unset_system_trait,
)
from environments.models import Environment

_TRAIT_KEY = "flagsmith_cohort_abc"
_OTHER_KEY = "flagsmith_cohort_other"


def test_set_system_trait__postgres_unknown_identifier__creates_identity(
    environment: Environment,
) -> None:
    # Given / When
    set_system_trait(environment, _TRAIT_KEY, ["newcomer"])

    # Then
    identity = Identity.objects.get(environment=environment, identifier="newcomer")
    assert identity.system_traits == {_TRAIT_KEY: True}


def test_set_system_trait__postgres_called_twice__stays_set(
    environment: Environment,
) -> None:
    # Given
    set_system_trait(environment, _TRAIT_KEY, ["member"])

    # When
    set_system_trait(environment, _TRAIT_KEY, ["member"])

    # Then
    identity = Identity.objects.get(environment=environment, identifier="member")
    assert identity.system_traits == {_TRAIT_KEY: True}


def test_unset_system_trait__postgres_other_traits_present__removes_given_key(
    environment: Environment,
) -> None:
    # Given
    set_system_trait(environment, _TRAIT_KEY, ["member"])
    set_system_trait(environment, _OTHER_KEY, ["member"])

    # When
    unset_system_trait(environment, _TRAIT_KEY, ["member"])

    # Then
    identity = Identity.objects.get(environment=environment, identifier="member")
    assert identity.system_traits == {_OTHER_KEY: True}


def test_unset_system_trait__postgres_trait_never_set__creates_no_identity(
    environment: Environment,
) -> None:
    # Given / When
    unset_system_trait(environment, _TRAIT_KEY, ["stranger"])

    # Then
    assert not Identity.objects.filter(
        environment=environment, identifier="stranger"
    ).exists()


def test_set_system_trait__edge_unknown_identifier__creates_document(
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    environment = dynamo_enabled_project_environment_one

    # When
    set_system_trait(environment, _TRAIT_KEY, ["newcomer"])

    # Then
    document = dynamodb_identity_wrapper.get_item(f"{environment.api_key}_newcomer")
    assert document is not None
    assert document["system_traits"] == {_TRAIT_KEY: True}


def test_set_system_trait__edge_called_twice__stays_set(
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    environment = dynamo_enabled_project_environment_one
    set_system_trait(environment, _TRAIT_KEY, ["member"])

    # When
    set_system_trait(environment, _TRAIT_KEY, ["member"])

    # Then
    document = dynamodb_identity_wrapper.get_item(f"{environment.api_key}_member")
    assert document is not None
    assert document["system_traits"] == {_TRAIT_KEY: True}


def test_unset_system_trait__edge_other_traits_present__removes_given_key(
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    environment = dynamo_enabled_project_environment_one
    set_system_trait(environment, _TRAIT_KEY, ["member"])
    set_system_trait(environment, _OTHER_KEY, ["member"])

    # When
    unset_system_trait(environment, _TRAIT_KEY, ["member"])

    # Then
    document = dynamodb_identity_wrapper.get_item(f"{environment.api_key}_member")
    assert document is not None
    assert document["system_traits"] == {_OTHER_KEY: True}


def test_unset_system_trait__edge_trait_never_set__creates_no_document(
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> None:
    # Given
    environment = dynamo_enabled_project_environment_one

    # When
    unset_system_trait(environment, _TRAIT_KEY, ["stranger"])

    # Then
    assert dynamodb_identity_wrapper.get_item(f"{environment.api_key}_stranger") is None
