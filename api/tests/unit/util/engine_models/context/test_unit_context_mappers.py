from environments.models import Environment
from util.engine_models.context.mappers import map_environment_identity_to_context
from util.engine_models.identities.models import IdentityModel
from util.engine_models.identities.traits.models import TraitModel


def test_map_environment_identity_to_context__system_traits__merged_with_system_winning(
    environment: Environment,
) -> None:
    # Given
    identity = IdentityModel(
        identifier="user-1",
        environment_api_key=environment.api_key,
        identity_traits=[
            TraitModel(trait_key="plan", trait_value="free"),
            TraitModel(trait_key="flagsmith_cohort_a", trait_value="user-written"),
        ],
        system_traits={"flagsmith_cohort_a": True},
    )

    # When
    context = map_environment_identity_to_context(
        environment=environment, identity=identity, override_traits=None
    )

    # Then
    identity_context = context["identity"]
    assert identity_context is not None
    assert identity_context["traits"] == {
        "plan": "free",
        "flagsmith_cohort_a": True,
    }
