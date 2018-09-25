from django.test import TestCase

from .models import Organisation


class OrganisationTestCase(TestCase):
    def test_can_create_organisation_with_and_without_webhook_notification_email(self):
        organisation_1 = Organisation.objects.create(name="Test org")
        organisation_2 = Organisation.objects.create(name="Test org with webhook email",
                                                     webhook_notification_email="test@org.com")

        self.assertTrue(organisation_1.name)
        self.assertTrue(organisation_2.name)
