from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class HealthChecksTestCase(APITestCase):
    def test_health_check_endpoint_returns_200(self):
        # Given
        base_url = reverse("health:health_check_home")
        url = base_url + "?format=json"

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK
