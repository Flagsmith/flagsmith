import pytest
from django.conf import settings

from e2etests.e2e_seed_data import seed_data
from experimentation.models import WarehouseConnection
from features.feature_types import MULTIVARIATE
from features.models import Feature
from organisations.models import OrganisationSubscriptionInformationCache
from projects.models import Project
from users.models import FFAdminUser


@pytest.mark.saas_mode
@pytest.mark.django_db
def test_seed_data__saas__lifts_e2e_organisation_plan_limits() -> None:
    # Given / When
    seed_data()

    # Then
    e2e_user = FFAdminUser.objects.get(email=settings.E2E_USER)
    organisation = e2e_user.organisations.get()
    subscription_cache = organisation.subscription_information_cache
    assert subscription_cache.allowed_seats == 8
    assert subscription_cache.allowed_projects is None
    assert subscription_cache.audit_log_visibility_days is None
    assert subscription_cache.feature_history_visibility_days is None


@pytest.mark.django_db
def test_seed_data__self_hosted__creates_no_subscription_information_cache() -> None:
    # Given / When
    seed_data()

    # Then
    assert not OrganisationSubscriptionInformationCache.objects.exists()


@pytest.mark.django_db
def test_seed_data__default__creates_experiments_project_with_multivariate_feature() -> (
    None
):
    # Given / When
    seed_data()

    # Then
    e2e_user = FFAdminUser.objects.get(email=settings.E2E_USER)
    project = Project.objects.get(
        name="My Test Project 8 Experiments",
        organisation__in=e2e_user.organisations.all(),
    )
    assert list(project.environments.values_list("name", flat=True)) == ["Development"]
    feature = Feature.objects.get(project=project, name="experiment_checkout")
    assert feature.type == MULTIVARIATE
    assert feature.initial_value == "control"
    assert {
        option.key: option.value for option in feature.multivariate_options.all()
    } == {"variant_a": "a", "variant_b": "b"}


@pytest.mark.parametrize(
    "expected_connections",
    [
        pytest.param(
            [("Development", "flagsmith", "connected")],
            marks=pytest.mark.saas_mode,
            id="saas",
        ),
        pytest.param([], id="self-hosted"),
    ],
)
@pytest.mark.django_db
def test_seed_data__deployment__seeds_expected_experiments_warehouse_connections(
    expected_connections: list[tuple[str, str, str]],
) -> None:
    # Given / When
    seed_data()

    # Then
    assert (
        list(
            WarehouseConnection.objects.filter(
                environment__project__name="My Test Project 8 Experiments"
            ).values_list("environment__name", "warehouse_type", "status")
        )
        == expected_connections
    )
