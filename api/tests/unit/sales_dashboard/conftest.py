import pytest

from organisations.models import Organisation
from sales_dashboard.forms import StartTrialForm


@pytest.fixture()
def in_trial_organisation(organisation: Organisation) -> Organisation:
    form = StartTrialForm(data={"max_seats": 20, "max_api_calls": 5_000_000})
    assert form.is_valid()
    form.save(organisation)
    organisation.refresh_from_db()
    organisation.subscription_information_cache.refresh_from_db()
    return organisation
