import pytest
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]

from environments.dynamodb import DynamoIdentityWrapper
from environments.identities.models import Identity
from environments.identities.system_traits import (
    set_system_trait,
    unset_system_trait,
)
from environments.models import Environment

_TRAIT_KEY = "flagsmith_cohort_abc"


def _stored_system_traits(
    environment: Environment, identifier: str
) -> dict[str, object] | None:
    """Read back whichever store this environment's identities live in."""
    wrapper = DynamoIdentityWrapper()
    if environment.project.enable_dynamo_db and wrapper.is_enabled:
        document = wrapper.get_item(f"{environment.api_key}_{identifier}")
        return None if document is None else dict(document.get("system_traits") or {})
    identity = Identity.objects.filter(
        environment=environment, identifier=identifier
    ).first()
    return None if identity is None else identity.system_traits


@pytest.fixture()
def edge_environment(
    dynamo_enabled_project_environment_one: Environment,
    dynamodb_identity_wrapper: DynamoIdentityWrapper,
) -> Environment:
    return dynamo_enabled_project_environment_one


# Both stores implement one contract, so every case runs against each.
_ENVIRONMENTS = [
    pytest.param(lazy_fixture("environment"), id="postgres"),
    pytest.param(lazy_fixture("edge_environment"), id="dynamodb"),
]


@pytest.mark.parametrize("target_environment", _ENVIRONMENTS)
def test_set_system_trait__unknown_identifier__stores_trait(
    target_environment: Environment,
) -> None:
    # Given / When
    set_system_trait(target_environment, _TRAIT_KEY, ["newcomer"])

    # Then
    assert _stored_system_traits(target_environment, "newcomer") == {_TRAIT_KEY: True}


@pytest.mark.parametrize("target_environment", _ENVIRONMENTS)
def test_set_system_trait__called_twice__stays_set(
    target_environment: Environment,
) -> None:
    # Given
    set_system_trait(target_environment, _TRAIT_KEY, ["member"])

    # When
    set_system_trait(target_environment, _TRAIT_KEY, ["member"])

    # Then
    assert _stored_system_traits(target_environment, "member") == {_TRAIT_KEY: True}


@pytest.mark.parametrize("target_environment", _ENVIRONMENTS)
def test_unset_system_trait__other_traits_present__removes_only_given_key(
    target_environment: Environment,
) -> None:
    # Given
    other_key = "flagsmith_cohort_other"
    set_system_trait(target_environment, _TRAIT_KEY, ["member"])
    set_system_trait(target_environment, other_key, ["member"])

    # When
    unset_system_trait(target_environment, _TRAIT_KEY, ["member"])

    # Then
    assert _stored_system_traits(target_environment, "member") == {other_key: True}


@pytest.mark.parametrize("target_environment", _ENVIRONMENTS)
def test_unset_system_trait__trait_never_set__leaves_identity_unchanged(
    target_environment: Environment,
) -> None:
    # Given / When
    unset_system_trait(target_environment, _TRAIT_KEY, ["stranger"])

    # Then
    assert _stored_system_traits(target_environment, "stranger") is None


@pytest.mark.parametrize("target_environment", _ENVIRONMENTS)
def test_set_system_trait__no_identifiers__creates_no_identity(
    target_environment: Environment,
) -> None:
    # Given / When
    set_system_trait(target_environment, _TRAIT_KEY, [])

    # Then
    assert not Identity.objects.filter(environment=target_environment).exists()


@pytest.mark.parametrize("target_environment", _ENVIRONMENTS)
def test_unset_system_trait__no_identifiers__creates_no_identity(
    target_environment: Environment,
) -> None:
    # Given / When
    unset_system_trait(target_environment, _TRAIT_KEY, [])

    # Then
    assert not Identity.objects.filter(environment=target_environment).exists()
