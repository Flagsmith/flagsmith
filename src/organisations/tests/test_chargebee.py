from datetime import datetime
from unittest import TestCase, mock

import pytest
from pytz import UTC

from organisations.chargebee import get_max_seats_for_plan, get_subscription_data_from_hosted_page


class MockChargeBeePlanResponse:
    def __init__(self, max_seats=0):
        self.max_seats = max_seats
        self.plan = MockChargeBeePlan(max_seats)


class MockChargeBeePlan:
    def __init__(self, max_seats=0):
        self.meta_data = {
            "seats": max_seats
        }


class MockChargeBeeHostedPageResponse:
    def __init__(self, subscription_id='subscription-id', plan_id='plan-id', created_at=datetime.utcnow()):
        self.hosted_page = MockChargeBeeHostedPage(subscription_id=subscription_id, plan_id=plan_id,
                                                   created_at=created_at)


class MockChargeBeeHostedPage:
    def __init__(self, hosted_page_id='some-id', subscription_id='subscription-id', plan_id='plan-id',
                 created_at=datetime.utcnow()):
        self.id = hosted_page_id
        self.content = MockChargeBeeHostedPageContent(subscription_id=subscription_id, plan_id=plan_id,
                                                      created_at=created_at)


class MockChargeBeeHostedPageContent:
    def __init__(self, subscription_id='subscription-id', plan_id='plan-id', created_at=datetime.utcnow()):
        self.subscription = MockChargeBeeSubscription(subscription_id=subscription_id, plan_id=plan_id,
                                                      created_at=created_at)


class MockChargeBeeSubscription:
    def __init__(self, subscription_id='subscription-id', plan_id='plan-id', created_at=datetime.utcnow()):
        self.id = subscription_id
        self.plan_id = plan_id
        self.created_at = datetime.timestamp(created_at)


@pytest.mark.django_db
class ChargeBeeTestCase(TestCase):
    @mock.patch('organisations.chargebee.chargebee')
    def test_get_max_seats_for_plan_returns_max_seats_for_plan(self, mock_cb):
        # Given
        plan_id = 'startup'
        expected_max_seats = 3

        mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(expected_max_seats)

        # When
        max_seats = get_max_seats_for_plan(plan_id)

        # Then
        assert max_seats == expected_max_seats

    @mock.patch('organisations.chargebee.chargebee')
    def test_get_subscription_data_from_hosted_page_returns_expected_values(self, mock_cb):
        # Given
        subscription_id = 'abc123'
        plan_id = 'startup'
        expected_max_seats = 3
        created_at = datetime.now(tz=UTC)

        mock_cb.HostedPage.retrieve.return_value = MockChargeBeeHostedPageResponse(subscription_id=subscription_id,
                                                                                   plan_id=plan_id,
                                                                                   created_at=created_at)
        mock_cb.Plan.retrieve.return_value = MockChargeBeePlanResponse(expected_max_seats)

        # When
        subscription_data = get_subscription_data_from_hosted_page('hosted_page_id')

        # Then
        assert subscription_data['subscription_id'] == subscription_id
        assert subscription_data['plan'] == plan_id
        assert subscription_data['max_seats'] == expected_max_seats
        assert subscription_data['subscription_date'] == created_at
