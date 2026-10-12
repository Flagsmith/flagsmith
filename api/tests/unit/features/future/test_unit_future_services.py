import pytest
from rest_framework.exceptions import ValidationError

from core.dataclasses import AuthorData
from environments.models import Environment
from features.future.services import update_flag
from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from users.models import FFAdminUser


@pytest.mark.parametrize(
    "environment_fixture_name",
    ["environment", "environment_v2_versioning"],
)
def test_update_flag__some_variants_weighted_past_100__raises(
    environment_fixture_name: str,
    multivariate_feature: Feature,
    multivariate_options: list[MultivariateFeatureOption],
    admin_user: FFAdminUser,
    request: pytest.FixtureRequest,
) -> None:
    # Given a flag weighting two of its variants 50/50
    environment: Environment = request.getfixturevalue(environment_fixture_name)
    author = AuthorData(user=admin_user)
    option_a, option_b, option_c = multivariate_options
    update_flag(
        environment=environment,
        feature=multivariate_feature,
        changes={
            "environment_default": {
                "variants": [
                    {"id": option_a.id, "weight": 50.0},
                    {"id": option_b.id, "weight": 50.0},
                    {"id": option_c.id, "weight": 0.0},
                ]
            }
        },
        replace=False,
        author=author,
        system=False,
    )

    # When only one variant is reweighted, past the remaining 50%
    # Then the variants not given keep their weights, and the total is refused
    with pytest.raises(ValidationError, match="got 110.0"):
        update_flag(
            environment=environment,
            feature=multivariate_feature,
            changes={
                "environment_default": {
                    "variants": [{"id": option_a.id, "weight": 60.0}]
                }
            },
            replace=False,
            author=author,
            system=False,
        )
