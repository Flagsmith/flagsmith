import pytest

from organisations.chargebee.metadata import ChargebeePlanMetadata


@pytest.fixture
def chargebee_object_metadata():
    return ChargebeePlanMetadata(seats=10, api_calls=100, projects=10)
