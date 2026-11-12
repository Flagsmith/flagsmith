import pytest
from django.conf import settings

from e2etests.e2e_seed_data import seed_data
from organisations.models import OrganisationSubscriptionInformationCache
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
