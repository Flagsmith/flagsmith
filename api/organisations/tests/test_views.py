import json
from datetime import datetime, timedelta
from unittest import TestCase, mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from pytz import UTC
from rest_framework import status
from rest_framework.test import APIClient, override_settings

from environments.models import Environment
from features.models import Feature, FeatureSegment
from organisations.invites.models import Invite
from organisations.models import Organisation, OrganisationRole, Subscription
from projects.models import Project
from segments.models import Segment
from users.models import FFAdminUser, UserPermissionGroup
from util.tests import Helper

User = get_user_model()


@pytest.mark.django_db
class OrganisationTestCase(TestCase):
    post_template = '{ "name" : "%s", "webhook_notification_email": "%s" }'
    put_template = '{ "name" : "%s"}'

    def setUp(self):
        self.client = APIClient()
        self.user = Helper.create_ffadminuser()
        self.client.force_authenticate(user=self.user)

    def test_should_return_organisation_list_when_requested(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")
        self.user.add_organisation(organisation)

        # When
        response = self.client.get("/api/v1/organisations/")

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert "count" in response.data and response.data["count"] == 1

        # and certain required fields are there
        response_json = response.json()
        org_data = response_json["results"][0]
        assert "persist_trait_data" in org_data

    def test_non_superuser_can_create_new_organisation_by_default(self):
        # Given
        user = User.objects.create(email="test@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        org_name = "Test create org"
        webhook_notification_email = "test@email.com"
        url = reverse("api-v1:organisations:organisation-list")
        data = {
            "name": org_name,
            "webhook_notification_email": webhook_notification_email,
        }

        # When
        response = client.post(url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert (
            Organisation.objects.get(name=org_name).webhook_notification_email
            == webhook_notification_email
        )

    @override_settings(RESTRICT_ORG_CREATE_TO_SUPERUSERS=True)
    def test_create_new_orgnisation_returns_403_with_non_superuser(self):
        # Given
        user = User.objects.create(email="test@example.com")
        client = APIClient()
        client.force_authenticate(user=user)

        org_name = "Test create org"
        url = reverse("api-v1:organisations:organisation-list")
        data = {
            "name": org_name,
        }

        # When
        response = client.post(url, data=data)
        # Then
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            "You do not have permission to perform this action."
            == response.json()["detail"]
        )

    def test_should_update_organisation_data(self):
        # Given
        original_organisation_name = "test org"
        new_organisation_name = "new test org"
        organisation = Organisation.objects.create(name=original_organisation_name)
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse(
            "api-v1:organisations:organisation-detail", args=[organisation.pk]
        )
        data = {"name": new_organisation_name, "restrict_project_create_to_admin": True}

        # When
        response = self.client.put(url, data=data)

        # Then
        organisation.refresh_from_db()
        assert response.status_code == status.HTTP_200_OK
        assert organisation.name == new_organisation_name
        assert organisation.restrict_project_create_to_admin

    @override_settings()
    def test_should_invite_users(self):
        # Given
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

        org_name = "test_org"
        organisation = Organisation.objects.create(name=org_name)
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse(
            "api-v1:organisations:organisation-invite", args=[organisation.pk]
        )
        data = {
            "emails": ["test@example.com"],
            "frontend_base_url": "https://example.com",
        }

        # When
        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response.status_code == status.HTTP_201_CREATED
        assert Invite.objects.filter(email="test@example.com").exists()

    @override_settings()
    def test_should_fail_if_invite_exists_already(self):
        # Given
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None
        organisation = Organisation.objects.create(name="test org")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        email = "test_2@example.com"
        data = {"emails": [email], "frontend_base_url": "https://example.com"}
        url = reverse(
            "api-v1:organisations:organisation-invite", args=[organisation.pk]
        )

        # When
        response_success = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )
        response_fail = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert response_success.status_code == status.HTTP_201_CREATED
        assert response_fail.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            Invite.objects.filter(email=email, organisation=organisation).count() == 1
        )

    @override_settings()
    def test_should_return_all_invites_and_can_resend(self):
        # Given
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

        organisation = Organisation.objects.create(name="Test org 2")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)

        invite_1 = Invite.objects.create(
            email="test_1@example.com",
            frontend_base_url="https://www.example.com",
            organisation=organisation,
        )
        Invite.objects.create(
            email="test_2@example.com",
            frontend_base_url="https://www.example.com",
            organisation=organisation,
        )

        # When
        invite_list_response = self.client.get(
            "/api/v1/organisations/%s/invites/" % organisation.id
        )
        invite_resend_response = self.client.post(
            "/api/v1/organisations/%s/invites/%s/resend/"
            % (organisation.id, invite_1.id)
        )

        # Then
        assert invite_list_response.status_code == status.HTTP_200_OK
        assert invite_resend_response.status_code == status.HTTP_200_OK

    def test_remove_user_from_an_organisation_also_removes_from_group(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")
        group = UserPermissionGroup.objects.create(
            name="Test Group", organisation=organisation
        )
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        user_2 = FFAdminUser.objects.create(email="test@example.com")
        user_2.add_organisation(organisation)
        # Add users to the group
        group.users.add(user_2)
        group.users.add(self.user)
        url = reverse(
            "api-v1:organisations:organisation-remove-users", args=[organisation.pk]
        )

        data = [{"id": user_2.pk}]

        # When
        res = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_200_OK
        assert organisation not in user_2.organisations.all()
        assert group not in user_2.permission_groups.all()
        # Test that other users are still part of the group
        assert group in self.user.permission_groups.all()

    @override_settings()
    def test_can_invite_user_as_admin(self):
        # Given
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

        organisation = Organisation.objects.create(name="Test org")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse(
            "api-v1:organisations:organisation-invite", args=[organisation.pk]
        )
        invited_email = "test@example.com"

        data = {
            "invites": [{"email": invited_email, "role": OrganisationRole.ADMIN.name}],
            "frontend_base_url": "http://blah.com",
        }

        # When
        self.client.post(url, data=json.dumps(data), content_type="application/json")

        # Then
        assert Invite.objects.filter(email=invited_email).exists()

        # and
        assert (
            Invite.objects.get(email=invited_email).role == OrganisationRole.ADMIN.name
        )

    @override_settings()
    def test_can_invite_user_as_user(self):
        # Given
        settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["invite"] = None

        organisation = Organisation.objects.create(name="Test org")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse(
            "api-v1:organisations:organisation-invite", args=[organisation.pk]
        )
        invited_email = "test@example.com"

        data = {
            "invites": [{"email": invited_email, "role": OrganisationRole.USER.name}],
            "frontend_base_url": "http://blah.com",
        }

        # When
        self.client.post(url, data=json.dumps(data), content_type="application/json")

        # Then
        assert Invite.objects.filter(email=invited_email).exists()

        # and
        assert (
            Invite.objects.get(email=invited_email).role == OrganisationRole.USER.name
        )

    def test_user_can_get_projects_for_an_organisation(self):
        # Given
        organisation = Organisation.objects.create(name="Test org")

        self.user.add_organisation(organisation, OrganisationRole.USER)
        url = reverse(
            "api-v1:organisations:organisation-projects", args=[organisation.pk]
        )

        # When
        res = self.client.get(url)

        # Then
        assert res.status_code == status.HTTP_200_OK

    @mock.patch("app_analytics.influxdb_wrapper.influxdb_client")
    def test_should_get_usage_for_organisation(self, mock_influxdb_client):
        # Given
        org_name = "test_org"
        organisation = Organisation.objects.create(name=org_name)
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse("api-v1:organisations:organisation-usage", args=[organisation.pk])

        influx_org = settings.INFLUXDB_ORG
        read_bucket = settings.INFLUXDB_BUCKET + "_downsampled_15m"
        query = (
            f'from(bucket:"{read_bucket}") '
            f"|> range(start: -30d, stop: now()) "
            f'|> filter(fn:(r) => r._measurement == "api_call")         '
            f'|> filter(fn: (r) => r["_field"] == "request_count")         '
            f'|> filter(fn: (r) => r["organisation_id"] == "{organisation.id}") '
            f'|> drop(columns: ["organisation", "project", "project_id", "environment", "environment_id"])'
            f"|> sum()"
        )

        # When
        response = self.client.get(url, content_type="application/json")

        # Then
        assert response.status_code == status.HTTP_200_OK
        mock_influxdb_client.query_api.return_value.query.assert_called_once_with(
            org=influx_org, query=query
        )

    @override_settings(ENABLE_CHARGEBEE=True)
    @mock.patch("organisations.serializers.get_subscription_data_from_hosted_page")
    def test_update_subscription_gets_subscription_data_from_chargebee(
        self, mock_get_subscription_data
    ):
        # Given
        organisation = Organisation.objects.create(name="Test org")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        url = reverse(
            "api-v1:organisations:organisation-update-subscription",
            args=[organisation.pk],
        )

        hosted_page_id = "some-id"
        data = {"hosted_page_id": hosted_page_id}

        customer_id = "customer-id"

        subscription_id = "subscription-id"
        mock_get_subscription_data.return_value = {
            "subscription_id": subscription_id,
            "plan": "plan-id",
            "max_seats": 3,
            "subscription_date": datetime.now(tz=UTC),
            "customer_id": customer_id,
        }

        # When
        res = self.client.post(url, data=data)

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        mock_get_subscription_data.assert_called_with(hosted_page_id=hosted_page_id)

        # and
        assert (
            organisation.has_subscription()
            and organisation.subscription.subscription_id == subscription_id
            and organisation.subscription.customer_id == customer_id
        )

    def test_delete_organisation(self):
        # GIVEN an organisation with a project, environment, feature, segment and feature segment
        organisation = Organisation.objects.create(name="Test organisation")
        self.user.add_organisation(organisation, OrganisationRole.ADMIN)
        project = Project.objects.create(name="Test project", organisation=organisation)
        environment = Environment.objects.create(
            name="Test environment", project=project
        )
        feature = Feature.objects.create(name="Test feature", project=project)
        segment = Segment.objects.create(name="Test segment", project=project)
        FeatureSegment.objects.create(
            feature=feature, segment=segment, environment=environment
        )

        delete_organisation_url = reverse(
            "api-v1:organisations:organisation-detail", args=[organisation.id]
        )

        # WHEN
        response = self.client.delete(delete_organisation_url)

        # THEN
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class ChargeBeeWebhookTestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.cb_user = User.objects.create(
            email="chargebee@bullet-train.io", username="chargebee"
        )
        self.admin_user = User.objects.create(
            email="admin@bullet-train.io", username="admin", is_staff=True
        )
        self.client.force_authenticate(self.cb_user)
        self.organisation = Organisation.objects.create(name="Test org")

        self.url = reverse("api-v1:chargebee-webhook")
        self.subscription_id = "subscription-id"
        self.old_plan_id = "old-plan-id"
        self.old_max_seats = 1
        self.subscription = Subscription.objects.create(
            organisation=self.organisation,
            subscription_id=self.subscription_id,
            plan=self.old_plan_id,
            max_seats=self.old_max_seats,
        )

    @mock.patch("organisations.models.get_max_seats_for_plan")
    def test_when_subscription_plan_is_changed_max_seats_updated(
        self, mock_get_max_seats
    ):
        # Given
        new_plan_id = "new-plan-id"
        new_max_seats = 3
        mock_get_max_seats.return_value = new_max_seats

        data = {
            "content": {
                "subscription": {
                    "status": "active",
                    "id": self.subscription_id,
                    "plan_id": new_plan_id,
                }
            }
        }

        # When
        res = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_200_OK

        # and
        self.subscription.refresh_from_db()
        assert self.subscription.plan == new_plan_id
        assert self.subscription.max_seats == new_max_seats

    def test_when_subscription_is_set_to_non_renewing_then_cancellation_date_set_and_alert_sent(
        self,
    ):
        # Given
        cancellation_date = datetime.now(tz=UTC) + timedelta(days=1)
        data = {
            "content": {
                "subscription": {
                    "status": "non_renewing",
                    "id": self.subscription_id,
                    "current_term_end": datetime.timestamp(cancellation_date),
                }
            }
        }

        # When
        self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        self.subscription.refresh_from_db()
        assert self.subscription.cancellation_date == cancellation_date

        # and
        assert len(mail.outbox) == 1

    def test_when_subscription_is_cancelled_then_cancellation_date_set_and_alert_sent(
        self,
    ):
        # Given
        cancellation_date = datetime.now(tz=UTC) + timedelta(days=1)
        data = {
            "content": {
                "subscription": {
                    "status": "cancelled",
                    "id": self.subscription_id,
                    "current_term_end": datetime.timestamp(cancellation_date),
                }
            }
        }

        # When
        self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        self.subscription.refresh_from_db()
        assert self.subscription.cancellation_date == cancellation_date

        # and
        assert len(mail.outbox) == 1

    def test_when_cancelled_subscription_is_renewed_then_subscription_activated_and_no_cancellation_email_sent(
        self,
    ):
        # Given
        self.subscription.cancellation_date = datetime.now(tz=UTC) - timedelta(days=1)
        self.subscription.save()
        mail.outbox.clear()

        data = {
            "content": {
                "subscription": {
                    "status": "active",
                    "id": self.subscription_id,
                }
            }
        }

        # When
        self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        self.subscription.refresh_from_db()
        assert not self.subscription.cancellation_date

        # and
        assert not mail.outbox

    def test_when_chargebee_webhook_received_with_unknown_subscription_id_then_404(
        self,
    ):
        # Given
        data = {
            "content": {"subscription": {"status": "active", "id": "some-random-id"}}
        }

        # When
        res = self.client.post(
            self.url, data=json.dumps(data), content_type="application/json"
        )

        # Then
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class OrganisationWebhookViewSetTestCase(TestCase):
    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test org")
        self.user = FFAdminUser.objects.create(email="test@test.com")
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.list_url = reverse(
            "api-v1:organisations:organisation-webhooks-list",
            args=[self.organisation.id],
        )

    def test_user_can_create_new_webhook(self):
        # Given
        data = {
            "url": "https://test.com/my-webhook",
        }

        # When
        response = self.client.post(self.list_url, data=data)

        # Then
        assert response.status_code == status.HTTP_201_CREATED
