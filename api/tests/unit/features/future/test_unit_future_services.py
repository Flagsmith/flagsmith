from core.dataclasses import AuthorData
from environments.identities.models import Identity
from environments.models import Environment
from features.future.services import update_flag
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from tests.types import VariantAssignmentFixture
from users.models import FFAdminUser


def test_update_flag__v2_versioning_multivariate_weight_increase__keeps_enrolled_identities_in_variant(
    environment_v2_versioning: Environment,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
    variant_assignment: VariantAssignmentFixture,
) -> None:
    # Given a multivariate feature split 50/50 between two variants, and the
    # variant each of a range of identities is bucketed into
    author = AuthorData(user=admin_user)
    option_a, option_b, option_c = multivariate_options
    # The fixture derives an option's value from its percentage, so two of them
    # share a value. Key them so a variant identifies which option won.
    for index, option in enumerate(multivariate_options):
        option.key = f"variant-{index}"
        option.save()
    update_flag(
        environment=environment_v2_versioning,
        feature=multivariate_feature,
        changes={
            "environment_default": {
                "enabled": True,
                "variants": [
                    {"id": option_a.id, "weight": 50.0},
                    {"id": option_b.id, "weight": 50.0},
                    {"id": option_c.id, "weight": 0.0},
                ],
            }
        },
        replace=False,
        author=author,
        overwrite_system_segment_overrides=False,
    )
    identities = [
        Identity.objects.create(
            identifier=f"identity-{i}", environment=environment_v2_versioning
        )
        for i in range(100)
    ]
    original_assignment = variant_assignment(identities, multivariate_feature.name)

    # When the first variant's allocation is increased to 60/40
    update_flag(
        environment=environment_v2_versioning,
        feature=multivariate_feature,
        changes={
            "environment_default": {
                "variants": [
                    {"id": option_a.id, "weight": 60.0},
                    {"id": option_b.id, "weight": 40.0},
                    {"id": option_c.id, "weight": 0.0},
                ],
            }
        },
        replace=False,
        author=author,
        overwrite_system_segment_overrides=False,
    )

    # Then identities already in the grown variant stay in it, and the only
    # movement is from the shrunk variant into the grown one
    new_assignment = variant_assignment(identities, multivariate_feature.name)
    movers = {
        key
        for key in original_assignment
        if new_assignment[key] != original_assignment[key]
    }
    assert movers
    assert all(original_assignment[key] == option_b.key for key in movers)
    assert all(new_assignment[key] == option_a.key for key in movers)
    assert all(
        new_assignment[key] == original_assignment[key]
        for key in original_assignment
        if key not in movers
    )
