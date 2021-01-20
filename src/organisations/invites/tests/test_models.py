from datetime import timedelta
from unittest import TestCase

import pytest
from django.utils import timezone

from organisations.invites.models import InviteLink
from organisations.models import Organisation


@pytest.mark.django_db
class InviteLinkTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test organisation")

    def test_is_expired_expiry_date_in_past(self):
        # Given
        yesterday = timezone.now() - timedelta(days=1)
        expired_link = InviteLink.objects.create(
            organisation=self.organisation, expires_at=yesterday
        )

        # When
        is_expired = expired_link.is_expired

        # Then
        assert is_expired

    def test_is_expired_expiry_date_in_future(self):
        # Given
        tomorrow = timezone.now() + timedelta(days=1)
        expired_link = InviteLink.objects.create(
            organisation=self.organisation, expires_at=tomorrow
        )

        # When
        is_expired = expired_link.is_expired

        # Then
        assert not is_expired

    def test_is_expired_no_expiry_date(self):
        # Given
        expired_link = InviteLink.objects.create(
            organisation=self.organisation, expires_at=None
        )

        # When
        is_expired = expired_link.is_expired

        # Then
        assert not is_expired
