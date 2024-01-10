import pyotp
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from audit.models import AuditLog, RelatedObjectType
from organisations.models import Organisation
from users.models import FFAdminUser


class LoginAuditTestCase(APITestCase):
    test_email = "test@example.com"
    password = FFAdminUser.objects.make_random_password()

    def setUp(self) -> None:
        self.organisation = Organisation.objects.create(name="Test Organisation")
        self.user = FFAdminUser.objects.create(email=self.test_email)
        self.user.add_organisation(self.organisation)
        self.user.set_password(self.password)
        self.user.save(update_fields=["password"])

    def tearDown(self) -> None:
        FFAdminUser.objects.all().delete()
        cache.clear()

    def test_password_login_success_audit(self):
        # Given
        new_login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")

        # When password correct
        response = self.client.post(login_url, data=new_login_data)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["key"]

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert audit_log.log == f"User logged in: {self.user.email}"

    def test_password_login_failure_audit(self):
        # Given
        new_login_data = {
            "email": self.test_email,
            "password": f"DEFINITELY NOT {self.password}",
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")

        # When password incorrect
        response = self.client.post(login_url, data=new_login_data)

        # Then
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["non_field_errors"] == [
            "Unable to login with provided credentials."
        ]

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert audit_log.log == f"User login failed (password): {self.user.email}"

    def test_mfa_login_success_audit(self):
        # setup MFA method
        totp = self._login_and_create_activate_mfa()
        self.client.logout()

        # Given
        new_login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")

        # When password correct with MFA enabled
        response = self.client.post(login_url, data=new_login_data)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert (ephemeral_token := response.json()["ephemeral_token"])

        # and not yet logged in so no audit log
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 0
        )

        # Given
        confirm_login_data = {"ephemeral_token": ephemeral_token, "code": totp.now()}
        login_confirm_url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")

        # When code correct
        login_confirm_response = self.client.post(
            login_confirm_url, data=confirm_login_data
        )

        # Then
        assert login_confirm_response.status_code == status.HTTP_200_OK
        assert login_confirm_response.json()["key"]

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert audit_log.log == f"User logged in: {self.user.email}"

    def test_mfa_login_failure_audit(self):
        # setup MFA method
        self._login_and_create_activate_mfa()
        self.client.logout()

        # Given
        new_login_data = {
            "email": self.test_email,
            "password": self.password,
        }
        login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")

        # When
        response = self.client.post(login_url, data=new_login_data)

        # Then
        assert response.status_code == status.HTTP_200_OK
        assert (ephemeral_token := response.json()["ephemeral_token"])

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 0
        )

        # Given
        confirm_login_data = {"ephemeral_token": ephemeral_token, "code": "WRONG"}
        login_confirm_url = reverse("api-v1:custom_auth:mfa-authtoken-login-code")

        # When
        login_confirm_response = self.client.post(
            login_confirm_url, data=confirm_login_data
        )

        # Then
        assert login_confirm_response.status_code == status.HTTP_400_BAD_REQUEST
        assert login_confirm_response.json()["non_field_errors"] == [
            "Invalid or expired code."
        ]

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert audit_log.log == f"User login failed (invalid_code): {self.user.email}"

    def _login_and_create_activate_mfa(self):
        # trench doesn't make it easy to create MFA methods so share these steps between tests

        # Given
        self.client.force_authenticate(user=self.user)
        create_mfa_method_url = reverse(
            "api-v1:custom_auth:mfa-activate", kwargs={"method": "app"}
        )

        # When
        create_mfa_response = self.client.post(create_mfa_method_url)

        # Then
        assert create_mfa_response.status_code == status.HTTP_200_OK
        secret = create_mfa_response.json()["secret"]

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER_MFA_METHOD.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER_MFA_METHOD.name
        assert audit_log.related_object_id == self.user.mfa_methods.first().pk
        assert audit_log.organisation_id == self.organisation.pk
        assert audit_log.log == f"New User MFA method created: {self.user.email} / app"

        # Given
        totp = pyotp.TOTP(secret)
        confirm_mfa_data = {"code": totp.now()}
        confirm_mfa_method_url = reverse(
            "api-v1:custom_auth:mfa-activate-confirm", kwargs={"method": "app"}
        )

        # When
        confirm_mfa_method_response = self.client.post(
            confirm_mfa_method_url, data=confirm_mfa_data
        )

        # Then
        assert confirm_mfa_method_response.status_code == status.HTTP_200_OK

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER_MFA_METHOD.name
            ).count()
            == 2
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER_MFA_METHOD.name
        assert audit_log.related_object_id == self.user.mfa_methods.first().pk
        assert audit_log.organisation_id == self.organisation.pk
        expected_logs = [
            f"User MFA method is_primary set true: {self.user.email} / app",
            f"User MFA method is_active set true: {self.user.email} / app",
        ]
        assert all([expected_log in audit_log.log for expected_log in expected_logs])

        return totp

    def test_create_update_mfa_audit(self):
        # setup/test MFA method and throttling
        self._login_and_create_activate_mfa()

        # Given
        remove_mfa_method_url = reverse(
            "api-v1:custom_auth:mfa-deactivate", kwargs={"method": "app"}
        )

        # When
        remove_mfa_method_response = self.client.post(remove_mfa_method_url)

        # Then
        assert remove_mfa_method_response.status_code == status.HTTP_204_NO_CONTENT

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER_MFA_METHOD.name
            ).count()
            == 3
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER_MFA_METHOD.name
        assert audit_log.related_object_id == self.user.mfa_methods.first().pk
        assert audit_log.organisation_id == self.organisation.pk
        expected_logs = [
            f"User MFA method is_primary set false: {self.user.email} / app",
            f"User MFA method is_active set false: {self.user.email} / app",
        ]
        assert all([expected_log in audit_log.log for expected_log in expected_logs])
