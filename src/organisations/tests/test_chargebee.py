from unittest import TestCase, mock

import pytest

from organisations.chargebee import get_max_seats_for_plan


class MockChargeBeePlan:
    def __init__(self, max_seats=0):
        self.max_seats = max_seats
        self.plan = self.Plan(max_seats)

    class Plan:
        def __init__(self, max_seats=0):
            self.meta_data = {
                "seats": max_seats
            }


@pytest.mark.django_db
class ChargebeeTestCase(TestCase):
    @mock.patch('organisations.chargebee.chargebee')
    def test(self, mock_cb):
        # Given
        plan_id = 'startup'
        expected_max_seats = 3

        mock_cb.Plan.retrieve.return_value = MockChargeBeePlan(expected_max_seats)

        # When
        max_seats = get_max_seats_for_plan(plan_id)

        # Then
        assert max_seats == expected_max_seats
