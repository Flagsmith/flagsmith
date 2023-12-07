from unittest import TestCase, mock

import pytest
from django.db.utils import IntegrityError

from audit.models import AuditLog, RelatedObjectType
from audit.tasks import create_audit_log_from_historical_record
from environments.models import Environment
from organisations.models import Organisation, OrganisationRole
from organisations.permissions.models import UserOrganisationPermission
from organisations.permissions.permissions import ORGANISATION_PERMISSIONS
from projects.models import (
    Project,
    ProjectPermissionModel,
    UserProjectPermission,
)
from projects.permissions import VIEW_PROJECT
from users.models import FFAdminUser, UserPermissionGroup


@pytest.mark.django_db
class FFAdminUserTestCase(TestCase):
    def setUp(self) -> None:
        self.user = FFAdminUser.objects.create(email="test@example.com")
        self.organisation = Organisation.objects.create(name="Test Organisation")

        self.project_1 = Project.objects.create(
            name="Test project 1", organisation=self.organisation
        )
        self.project_2 = Project.objects.create(
            name="Test project 2", organisation=self.organisation
        )

        self.environment_1 = Environment.objects.create(
            name="Test Environment 1", project=self.project_1
        )
        self.environment_2 = Environment.objects.create(
            name="Test Environment 2", project=self.project_2
        )

    def test_user_belongs_to_success(self):
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        assert self.user.belongs_to(self.organisation.id)

    def test_user_belongs_to_fail(self):
        assert not self.user.belongs_to(self.organisation.id)

    def test_get_permitted_projects_for_org_admin_returns_all_projects(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # When
        projects = self.user.get_permitted_projects(VIEW_PROJECT)

        # Then
        assert projects.count() == 2

    def test_get_permitted_projects_for_user_returns_only_projects_matching_permission(
        self,
    ):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.USER)
        user_project_permission = UserProjectPermission.objects.create(
            user=self.user, project=self.project_1
        )
        read_permission = ProjectPermissionModel.objects.get(key=VIEW_PROJECT)
        user_project_permission.permissions.set([read_permission])

        # When
        projects = self.user.get_permitted_projects(permission_key=VIEW_PROJECT)

        # Then
        assert projects.count() == 1

    def test_get_admin_organisations(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # When
        admin_orgs = self.user.get_admin_organisations()

        # Then
        assert self.organisation in admin_orgs

    def test_get_permitted_environments_for_org_admin_returns_all_environments_for_project(
        self,
    ):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # When
        environments = self.user.get_permitted_environments(
            "VIEW_ENVIRONMENT", project=self.project_1
        )

        # Then
        assert environments.count() == self.project_1.environments.count()

    def test_get_permitted_environments_for_user_returns_only_environments_matching_permission(
        self,
    ):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.USER)

        # When
        environments = self.user.get_permitted_environments(
            "VIEW_ENVIRONMENT", project=self.project_1
        )

        # Then
        assert len(list(environments)) == 0

    def test_unique_user_organisation(self):
        # Given organisation and user

        # When
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # Then
        with pytest.raises(IntegrityError):
            self.user.add_organisation(self.organisation, OrganisationRole.USER)

    def test_has_organisation_permission_is_true_for_organisation_admin(self):
        # Given
        self.user.add_organisation(self.organisation, OrganisationRole.ADMIN)

        # Then
        assert all(
            self.user.has_organisation_permission(
                organisation=self.organisation, permission_key=permission_key
            )
            for permission_key, _ in ORGANISATION_PERMISSIONS
        )

    def test_has_organisation_permission_is_true_when_user_has_permission(self):
        # Given
        self.user.add_organisation(self.organisation)
        user_organisation_permission = UserOrganisationPermission.objects.create(
            user=self.user, organisation=self.organisation
        )
        for permission_key, _ in ORGANISATION_PERMISSIONS:
            user_organisation_permission.permissions.through.objects.create(
                permissionmodel_id=permission_key,
                userorganisationpermission=user_organisation_permission,
            )

        # Then
        assert all(
            self.user.has_organisation_permission(
                organisation=self.organisation, permission_key=permission_key
            )
            for permission_key, _ in ORGANISATION_PERMISSIONS
        )

    def test_has_organisation_permission_is_false_when_user_does_not_have_permission(
        self,
    ):
        # Given
        self.user.add_organisation(self.organisation)

        # Then
        assert not any(
            self.user.has_organisation_permission(
                organisation=self.organisation, permission_key=permission_key
            )
            for permission_key, _ in ORGANISATION_PERMISSIONS
        )

    @mock.patch("core.models._get_request_user")
    def test_create_user_audit_log(self, mock_get_request_user):
        # Given
        mock_get_request_user.return_value = self.user

        with mock.patch(
            "audit.tasks.create_audit_log_from_historical_record.delay",
            wraps=create_audit_log_from_historical_record.delay,
        ) as mock_create_audit_log:
            # When
            created_user = FFAdminUser.objects.create(email="test2@example.com")

            # Then
            # audit log called once for create user
            assert mock_create_audit_log.call_count == 1
            mock_create_audit_log.assert_called_with(
                kwargs={
                    "history_instance_id": created_user.history.last().pk,
                    "history_user_id": self.user.pk,
                    "history_record_class_path": "users.models.HistoricalFFAdminUser",
                },
                delay_until=None,
            )

        # no audit log for create user because no organisation associated at that moment
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 0
        )

    @mock.patch("core.models._get_request_user")
    def test_delete_user_audit_log(self, mock_get_request_user):
        # Given
        mock_get_request_user.return_value = None
        created_user = FFAdminUser.objects.create(email="test2@example.com")
        created_user.add_organisation(self.organisation)
        another_organisation = Organisation.objects.create(name="Another Organisation")
        created_user.add_organisation(another_organisation)
        created_user_pk = created_user.pk
        # delete request comes from admin user
        mock_get_request_user.return_value = self.user

        with mock.patch(
            "audit.tasks.create_audit_log_from_historical_record.delay",
            wraps=create_audit_log_from_historical_record.delay,
        ) as mock_create_audit_log:
            # When
            created_user.delete()

            # Then
            # audit log called twice for organisation removal and once for delete
            assert mock_create_audit_log.call_count == 3
            mock_create_audit_log.assert_called_with(
                kwargs={
                    "history_instance_id": mock.ANY,
                    "history_user_id": self.user.pk,
                    "history_record_class_path": "users.models.HistoricalFFAdminUser",
                },
                delay_until=None,
            )

        # check that organisation removal is logged for each organisation
        # no audit log for delete user because no organisation associated at that moment
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 2
        )
        # cross-organisation leak: on delete, the user is removed from all organisations in one operation,
        # and all organisations get the same log message
        expected_logs = [
            "User organisations updated: test2@example.com",
            # updates may appear in any order
            "removed: Test Organisation",
            "removed: Another Organisation",
        ]
        audit_logs = AuditLog.objects.all()[0:2]
        audit_log = audit_logs[0]
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == created_user_pk
        assert audit_log.organisation_id == another_organisation.pk
        assert all(expected_log in audit_log.log for expected_log in expected_logs)
        audit_log = audit_logs[1]
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == created_user_pk
        assert audit_log.organisation_id == self.organisation.pk
        assert all(expected_log in audit_log.log for expected_log in expected_logs)

    @mock.patch("core.models._get_request_user")
    def test_delete_self_audit_log(self, mock_get_request_user):
        # Given
        mock_get_request_user.return_value = None
        created_user = FFAdminUser.objects.create(email="test2@example.com")
        created_user.add_organisation(self.organisation)
        another_organisation = Organisation.objects.create(name="Another Organisation")
        created_user.add_organisation(another_organisation)
        created_user_pk = created_user.pk
        # delete request comes from self
        mock_get_request_user.return_value = created_user

        with mock.patch(
            "audit.tasks.create_audit_log_from_historical_record.delay",
            wraps=create_audit_log_from_historical_record.delay,
        ) as mock_create_audit_log:
            # When
            created_user.delete()

            # Then
            # audit log called twice for organisation removal and once for delete
            assert mock_create_audit_log.call_count == 3
            mock_create_audit_log.assert_called_with(
                kwargs={
                    "history_instance_id": mock.ANY,
                    "history_user_id": created_user_pk,
                    "history_record_class_path": "users.models.HistoricalFFAdminUser",
                },
                delay_until=None,
            )

        # check that organisation removal is logged for each organisation
        # no audit log for delete user because no organisation associated at that moment
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 2
        )
        # cross-organisation leak: on delete, the user is removed from all organisations in one operation,
        # and all organisations get the same log message
        expected_logs = [
            "User organisations updated: test2@example.com",
            # updates may appear in any order
            "removed: Test Organisation",
            "removed: Another Organisation",
        ]
        audit_logs = AuditLog.objects.all()[0:2]
        audit_log = audit_logs[0]
        assert audit_log
        assert audit_log.author_id is None
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == created_user_pk
        assert audit_log.organisation_id == another_organisation.pk
        assert all(expected_log in audit_log.log for expected_log in expected_logs)
        audit_log = audit_logs[1]
        assert audit_log
        assert audit_log.author_id is None
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == created_user_pk
        assert audit_log.organisation_id == self.organisation.pk
        assert all(expected_log in audit_log.log for expected_log in expected_logs)

    @mock.patch("core.models._get_request_user")
    def test_update_user_audit_log(self, mock_get_request_user):
        # Given
        mock_get_request_user.return_value = self.user
        self.user.add_organisation(self.organisation)
        another_organisation = Organisation.objects.create(name="Another Organisation")
        self.user.add_organisation(another_organisation)

        # When
        self.user.username = "test_username"
        self.user.email = "test-changed@example.com"
        self.user.first_name = "Test First"
        self.user.last_name = "Test Last"
        self.user.github_user_id = "123456"
        self.user.google_user_id = "234567"
        self.user.save()

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 4
        )
        # check that log is created for each organisation
        expected_logs = [
            # updates may appear in any order
            "User username updated: test-changed@example.com",
            "User email updated: test-changed@example.com",
            "User first_name updated: test-changed@example.com",
            "User last_name updated: test-changed@example.com",
            "User github_user_id updated: test-changed@example.com",
            "User google_user_id updated: test-changed@example.com",
        ]
        audit_logs = AuditLog.objects.all()[0:2]
        audit_log = audit_logs[0]
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == another_organisation.pk
        assert all(expected_log in audit_log.log for expected_log in expected_logs)
        audit_log = audit_logs[1]
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert all(expected_log in audit_log.log for expected_log in expected_logs)

    @mock.patch("core.models._get_request_user")
    def test_update_user_organisations_audit_log(self, mock_get_request_user):
        # Given
        mock_get_request_user.return_value = self.user

        # When
        self.user.add_organisation(self.organisation)

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        # check that latest log relates to test organisation
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert (
            audit_log.log
            == f"User organisations updated: {self.user.email}; added: Test Organisation"
        )

        # Given
        another_organisation = Organisation.objects.create(name="Another Organisation")

        # When
        self.user.add_organisation(another_organisation)

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 2
        )
        # check that latest log relates to another organisation (and not test organisation)
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == another_organisation.pk
        assert (
            audit_log.log
            == f"User organisations updated: {self.user.email}; added: Another Organisation"
        )

        # When
        self.user.remove_organisation(self.organisation)

        # Then
        # check that latest log relates to test organisation (and not another organisation)
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 3
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == self.user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == self.user.pk
        assert audit_log.organisation_id == self.organisation.pk
        assert (
            audit_log.log
            == f"User organisations updated: {self.user.email}; removed: Test Organisation"
        )


@pytest.mark.django_db
def test_creating_a_user_calls_mailer_lite_subscribe(mocker):
    # Given
    mailer_lite_mock = mocker.patch("users.models.mailer_lite")
    # When
    user = FFAdminUser.objects.create(
        email="test@mail.com",
    )
    # Then
    mailer_lite_mock.subscribe.assert_called_with(user)


@pytest.mark.django_db
def test_user_add_organisation_does_not_call_mailer_lite_subscribe_for_unpaid_organisation(
    mocker,
):
    user = FFAdminUser.objects.create(email="test@example.com")
    organisation = Organisation.objects.create(name="Test Organisation")
    mailer_lite_mock = mocker.patch("users.models.mailer_lite")
    mocker.patch(
        "organisations.models.Organisation.is_paid",
        new_callable=mock.PropertyMock,
        return_value=False,
    )
    # When
    user.add_organisation(organisation, OrganisationRole.USER)

    # Then
    mailer_lite_mock.subscribe.assert_not_called()


@pytest.mark.django_db
def test_user_add_organisation_calls_mailer_lite_subscribe_for_paid_organisation(
    mocker,
):
    mailer_lite_mock = mocker.patch("users.models.mailer_lite")
    user = FFAdminUser.objects.create(email="test@example.com")
    organisation = Organisation.objects.create(name="Test Organisation")
    mocker.patch(
        "organisations.models.Organisation.is_paid",
        new_callable=mock.PropertyMock,
        return_value=True,
    )
    # When
    user.add_organisation(organisation, OrganisationRole.USER)

    # Then
    mailer_lite_mock.subscribe.assert_called_with(user)


def test_user_add_organisation_adds_user_to_the_default_user_permission_group(
    test_user, organisation, default_user_permission_group, user_permission_group
):
    # When
    test_user.add_organisation(organisation, OrganisationRole.USER)

    # Then
    assert default_user_permission_group in test_user.permission_groups.all()
    assert user_permission_group not in test_user.permission_groups.all()


def test_user_remove_organisation_removes_user_from_the_user_permission_group(
    user_permission_group, admin_user, organisation, default_user_permission_group
):
    # Given - two groups that belongs to the same organisation, but user
    # is only part of one(`user_permission_group`) them

    # When
    admin_user.remove_organisation(organisation)

    # Then
    # extra group did not cause any errors and the user is removed from the group
    assert user_permission_group not in admin_user.permission_groups.all()


@pytest.mark.django_db
def test_delete_user():
    # create a couple of users
    email1 = "test1@example.com"
    email2 = "test2@example.com"
    email3 = "test3@example.com"
    user1 = FFAdminUser.objects.create(email=email1)
    user2 = FFAdminUser.objects.create(email=email2)
    user3 = FFAdminUser.objects.create(email=email3)

    # create some organisations
    org1 = Organisation.objects.create(name="org1")
    org2 = Organisation.objects.create(name="org2")
    org3 = Organisation.objects.create(name="org3")

    # add the test user 1 to all the organisations (cannot use Organisation.users reverse accessor)
    user1.organisations.add(org1, org2, org3)

    # add test user 2 to org2 and user 3 to to org1
    user2.organisations.add(org2)
    user3.organisations.add(org1)

    # Configuration: org1: [user1, user3], org2: [user1, user2], org3: [user1]

    # Delete user2
    user2.delete(delete_orphan_organisations=True)
    assert not FFAdminUser.objects.filter(email=email2).exists()

    # All organisations remain since user 2 has org2 as only organization and it has 2 users
    assert Organisation.objects.filter(name="org3").count() == 1
    assert Organisation.objects.filter(name="org1").count() == 1
    assert Organisation.objects.filter(name="org2").count() == 1

    # Delete user1
    user1.delete(delete_orphan_organisations=True)
    assert not FFAdminUser.objects.filter(email=email1).exists()

    # organization org3 and org2 are deleted since its only user is user1
    assert Organisation.objects.filter(name="org3").count() == 0
    assert Organisation.objects.filter(name="org2").count() == 0

    # org1 remain
    assert Organisation.objects.filter(name="org1").count() == 1

    # user3 remain
    assert FFAdminUser.objects.filter(email=email3).exists()

    # Delete user3
    user3.delete(delete_orphan_organisations=False)
    assert not FFAdminUser.objects.filter(email=email3).exists()
    assert Organisation.objects.filter(name="org1").count() == 1


def test_user_create_calls_pipedrive_tracking(mocker, db, settings):
    # Given
    mocked_create_pipedrive_lead = mocker.patch("users.signals.create_pipedrive_lead")
    settings.ENABLE_PIPEDRIVE_LEAD_TRACKING = True

    # When
    FFAdminUser.objects.create(email="test@example.com")

    # Then
    mocked_create_pipedrive_lead.delay.assert_called()


def test_user_create_does_not_call_pipedrive_tracking_if_ignored_domain(
    mocker, db, settings
):
    # Given
    mocked_create_pipedrive_lead = mocker.patch("users.signals.create_pipedrive_lead")
    settings.ENABLE_PIPEDRIVE_LEAD_TRACKING = True
    settings.PIPEDRIVE_IGNORE_DOMAINS = ["example.com"]

    # When
    FFAdminUser.objects.create(email="test@example.com")

    # Then
    mocked_create_pipedrive_lead.delay.assert_not_called()


def test_user_email_domain_property():
    assert FFAdminUser(email="test@example.com").email_domain == "example.com"


@pytest.mark.django_db()
def test_create_update_delete_group_audit_log(mocker, organisation, admin_user):
    # Given
    mocker.patch("core.models._get_request_user", return_value=admin_user)

    # When
    group = UserPermissionGroup.objects.create(
        name="Test Group", organisation=organisation
    )

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GROUP.name
        ).count()
        == 1
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group.pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"New Group created: {group.name}"

    # When
    group.name = new_name = "Test~~Group"
    group.is_default = True
    group.save()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GROUP.name
        ).count()
        == 2
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group.pk
    assert audit_log.organisation_id == organisation.pk
    expected_logs = [
        # updates may appear in any order
        f"Group name updated: {new_name}",
        f"Group is_default set true: {new_name}",
    ]
    assert all(expected_log in audit_log.log for expected_log in expected_logs)

    # When
    second_user = FFAdminUser.objects.create(email="test2@example.com")
    second_user.add_organisation(organisation)
    group.add_users_by_id([admin_user.pk, second_user.pk])

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GROUP.name
        ).count()
        == 4
    )
    audit_logs = AuditLog.objects.all()[0:2]
    audit_log = audit_logs[0]
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group.pk
    assert audit_log.organisation_id == organisation.pk
    audit_log = audit_logs[1]
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group.pk
    assert audit_log.organisation_id == organisation.pk
    expected_logs = [
        # users may appear in any order
        f"Group users updated: {new_name}; added: {second_user.email}",
        f"Group users updated: {new_name}; added: {admin_user.email}",
    ]
    assert all(
        expected_log in [audit_logs[0].log, audit_logs[1].log]
        for expected_log in expected_logs
    )

    # When
    group.remove_users_by_id([second_user.pk])

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GROUP.name
        ).count()
        == 5
    )
    audit_log = AuditLog.objects.first()
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group.pk
    assert audit_log.organisation_id == organisation.pk
    assert (
        audit_log.log
        == f"Group users updated: {new_name}; removed: {second_user.email}"
    )

    # When
    group_pk = group.pk
    group.delete()

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_type=RelatedObjectType.GROUP.name
        ).count()
        == 7
    )
    audit_logs = AuditLog.objects.all()[0:2]
    audit_log = audit_logs[0]
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group_pk
    assert audit_log.organisation_id == organisation.pk
    assert audit_log.log == f"Group deleted: {new_name}"
    audit_log = audit_logs[1]
    assert audit_log
    assert audit_log.author_id == admin_user.pk
    assert audit_log.related_object_type == RelatedObjectType.GROUP.name
    assert audit_log.related_object_id == group_pk
    assert audit_log.organisation_id == organisation.pk
    assert (
        audit_log.log == f"Group users updated: {new_name}; removed: {admin_user.email}"
    )
