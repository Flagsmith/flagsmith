import logging
import typing

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE, LifecycleModel, hook

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from organisations.models import (
    Organisation,
    OrganisationRole,
    UserOrganisation,
)
from permissions.permission_service import (
    get_organisation_permission_keys_for_user,
    get_permitted_environments_for_user,
    get_permitted_projects_for_user,
    is_user_environment_admin,
    is_user_organisation_admin,
    is_user_project_admin,
    user_has_organisation_permission,
)
from projects.models import Project, UserProjectPermission
from users.auth_type import AuthType
from users.exceptions import InvalidInviteError
from users.utils.mailer_lite import MailerLite

if typing.TYPE_CHECKING:
    from organisations.invites.models import (
        AbstractBaseInviteModel,
        Invite,
        InviteLink,
    )

logger = logging.getLogger(__name__)
mailer_lite = MailerLite()


class SignUpType(models.TextChoices):
    NO_INVITE = "NO_INVITE"
    INVITE_EMAIL = "INVITE_EMAIL"
    INVITE_LINK = "INVITE_LINK"


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        # Used to allow case insensitive login
        return self.get(email__iexact=email)


class FFAdminUser(LifecycleModel, AbstractUser):
    organisations = models.ManyToManyField(
        Organisation, related_name="users", blank=True, through=UserOrganisation
    )
    email = models.EmailField(unique=True, null=False)
    objects = UserManager()
    username = models.CharField(unique=True, max_length=150, null=True, blank=True)
    first_name = models.CharField(_("first name"), max_length=30)
    last_name = models.CharField(_("last name"), max_length=150)
    google_user_id = models.CharField(max_length=50, null=True, blank=True)
    github_user_id = models.CharField(max_length=50, null=True, blank=True)
    marketing_consent_given = models.BooleanField(
        default=False,
        help_text="Determines whether the user has agreed to receive marketing mails",
    )
    sign_up_type = models.CharField(
        choices=SignUpType.choices, max_length=100, blank=True, null=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "sign_up_type"]

    class Meta:
        ordering = ["id"]
        verbose_name = "Feature flag admin user"

    def __str__(self):
        return self.email

    @hook(AFTER_CREATE)
    def subscribe_to_mailing_list(self):
        mailer_lite.subscribe(self)

    @property
    def auth_type(self):
        if self.google_user_id:
            return AuthType.GOOGLE.value

        if self.github_user_id:
            return AuthType.GITHUB.value

        return AuthType.EMAIL.value

    @property
    def full_name(self):
        return self.get_full_name()

    @property
    def email_domain(self):
        return self.email.split("@")[1]

    def get_full_name(self):
        if not self.first_name:
            return None
        return " ".join([self.first_name, self.last_name]).strip()

    def join_organisation_from_invite_email(self, invite_email: "Invite"):
        if invite_email.email.lower() != self.email.lower():
            raise InvalidInviteError("Registered email does not match invited email")
        self.join_organisation_from_invite(invite_email)
        self.permission_groups.add(*invite_email.permission_groups.all())
        invite_email.delete()

    def join_organisation_from_invite_link(self, invite_link: "InviteLink"):
        self.join_organisation_from_invite(invite_link)

    def join_organisation_from_invite(self, invite: "AbstractBaseInviteModel"):
        organisation = invite.organisation
        subscription_metadata = organisation.subscription.get_subscription_metadata()

        if (
            len(settings.AUTO_SEAT_UPGRADE_PLANS) > 0
            and invite.organisation.num_seats >= subscription_metadata.seats
        ):
            organisation.subscription.add_single_seat()

        self.add_organisation(organisation, role=OrganisationRole(invite.role))

    def is_organisation_admin(self, organisation):
        return is_user_organisation_admin(self, organisation)

    def get_admin_organisations(self):
        return Organisation.objects.filter(
            userorganisation__user=self,
            userorganisation__role=OrganisationRole.ADMIN.name,
        )

    def add_organisation(self, organisation, role=OrganisationRole.USER):
        if organisation.is_paid:
            mailer_lite.subscribe(self)

        UserOrganisation.objects.create(
            user=self, organisation=organisation, role=role.name
        )
        default_groups = organisation.permission_groups.filter(is_default=True)
        self.permission_groups.add(*default_groups)

    def remove_organisation(self, organisation):
        UserOrganisation.objects.filter(user=self, organisation=organisation).delete()
        UserProjectPermission.objects.filter(
            user=self, project__organisation=organisation
        ).delete()
        UserEnvironmentPermission.objects.filter(
            user=self, environment__project__organisation=organisation
        ).delete()
        self.permission_groups.remove(*organisation.permission_groups.all())

    def get_organisation_role(self, organisation):
        user_organisation = self.get_user_organisation(organisation)
        if user_organisation:
            return user_organisation.role

    def get_organisation_role_by_id(self, organisation_id: int) -> typing.Optional[str]:
        user_organisation = self.get_user_organisation_by_id(organisation_id)
        return user_organisation.role

    def get_organisation_join_date(self, organisation):
        user_organisation = self.get_user_organisation(organisation)
        if user_organisation:
            return user_organisation.date_joined

    def get_user_organisation(self, organisation):
        try:
            return self.userorganisation_set.get(organisation=organisation)
        except UserOrganisation.DoesNotExist:
            logger.warning(
                "User %d is not part of organisation %d" % (self.id, organisation.id)
            )

    def get_permitted_projects(self, permission_key):
        return get_permitted_projects_for_user(self, permission_key)

    def has_project_permission(self, permission, project):
        if self.is_project_admin(project):
            return True
        return project in self.get_permitted_projects(permission)

    def has_environment_permission(
        self, permission: str, environment: Environment
    ) -> bool:
        return environment in get_permitted_environments_for_user(
            self, environment.project, permission
        )

    def is_project_admin(self, project: Project):
        return is_user_project_admin(self, project)

    def get_permitted_environments(
        self, permission_key: str, project: Project
    ) -> QuerySet[Environment]:
        return get_permitted_environments_for_user(self, project, permission_key)

    @staticmethod
    def send_alert_to_admin_users(subject, message):
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=FFAdminUser._get_admin_user_emails(),
            fail_silently=True,
        )

    @staticmethod
    def _get_admin_user_emails():
        return [
            user["email"]
            for user in FFAdminUser.objects.filter(is_staff=True).values("email")
        ]

    def belongs_to(self, organisation_id: int) -> bool:
        return organisation_id in self.organisations.all().values_list("id", flat=True)

    def is_environment_admin(
        self,
        environment: Environment,
    ):
        return is_user_environment_admin(self, environment)

    def has_organisation_permission(
        self, organisation: Organisation, permission_key: str
    ) -> bool:
        return user_has_organisation_permission(self, organisation, permission_key)
        if self.is_organisation_admin(organisation):
            return True

    def get_permission_keys_for_organisation(
        self, organisation: Organisation
    ) -> typing.Iterable[str]:
        return get_organisation_permission_keys_for_user(self, organisation)

    def is_group_admin(self, group_id) -> bool:
        return UserPermissionGroupMembership.objects.filter(
            ffadminuser=self, userpermissiongroup__id=group_id, group_admin=True
        ).exists()

    def make_group_admin(self, group_id: int):
        UserPermissionGroupMembership.objects.filter(
            ffadminuser=self, userpermissiongroup__id=group_id
        ).update(group_admin=True)

    def remove_as_group_admin(self, group_id: int):
        UserPermissionGroupMembership.objects.filter(
            ffadminuser=self, userpermissiongroup__id=group_id
        ).update(group_admin=False)


class UserPermissionGroupMembership(models.Model):
    userpermissiongroup = models.ForeignKey(
        "users.UserPermissionGroup",
        on_delete=models.CASCADE,
    )
    ffadminuser = models.ForeignKey("users.FFAdminUser", on_delete=models.CASCADE)
    group_admin = models.BooleanField(default=False)

    class Meta:
        db_table = "users_userpermissiongroup_users"


class UserPermissionGroup(models.Model):
    """
    Model to group users within an organisation for the purposes of permissioning.
    """

    name = models.CharField(max_length=200)
    users = models.ManyToManyField(
        "users.FFAdminUser",
        blank=True,
        related_name="permission_groups",
        through=UserPermissionGroupMembership,
        through_fields=["userpermissiongroup", "ffadminuser"],
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="permission_groups"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="If set to true, all new users will be added to this group",
    )

    external_id = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        help_text="Unique ID of the group in an external system",
    )

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings
        unique_together = ("organisation", "external_id")

    def add_users_by_id(self, user_ids: list):
        users_to_add = list(
            FFAdminUser.objects.filter(id__in=user_ids, organisations=self.organisation)
        )
        if len(user_ids) != len(users_to_add):
            missing_ids = set(users_to_add).difference({u.id for u in users_to_add})
            raise FFAdminUser.DoesNotExist(
                "Users %s do not exist in this organisation" % ", ".join(missing_ids)
            )
        self.users.add(*users_to_add)

    def remove_users_by_id(self, user_ids: list):
        self.users.remove(*user_ids)
