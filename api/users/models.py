import logging
import typing

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q, QuerySet
from django.utils.translation import gettext_lazy as _
from django_lifecycle import AFTER_CREATE, LifecycleModel, hook

from environments.models import Environment
from environments.permissions.models import (
    UserEnvironmentPermission,
    UserPermissionGroupEnvironmentPermission,
)
from organisations.models import (
    Organisation,
    OrganisationRole,
    UserOrganisation,
)
from organisations.permissions.models import (
    UserOrganisationPermission,
    UserPermissionGroupOrganisationPermission,
)
from projects.models import (
    Project,
    UserPermissionGroupProjectPermission,
    UserProjectPermission,
)
from users.auth_type import AuthType
from users.exceptions import InvalidInviteError
from users.utils.mailer_lite import MailerLite

logger = logging.getLogger(__name__)
mailer_lite = MailerLite()


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

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        ordering = ["id"]
        verbose_name = "Feature flag admin user"

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

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

    def get_full_name(self):
        if not self.first_name:
            return None
        return " ".join([self.first_name, self.last_name]).strip()

    def join_organisation(self, invite):
        organisation = invite.organisation

        if invite.email.lower() != self.email.lower():
            raise InvalidInviteError("Registered email does not match invited email")

        self.add_organisation(organisation, role=OrganisationRole(invite.role))
        invite.delete()

    def is_organisation_admin(self, organisation):
        return self.get_organisation_role(organisation) == OrganisationRole.ADMIN.name

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

    def remove_organisation(self, organisation):
        UserOrganisation.objects.filter(user=self, organisation=organisation).delete()
        UserProjectPermission.objects.filter(
            user=self, project__organisation=organisation
        ).delete()
        UserEnvironmentPermission.objects.filter(
            user=self, environment__project__organisation=organisation
        ).delete()

    def get_organisation_role(self, organisation):
        user_organisation = self.get_user_organisation(organisation)
        if user_organisation:
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

    def get_permitted_projects(self, permissions):
        """
        Get all projects that the user has the given permissions for.

        Rules:
            - User has the required permissions directly (UserProjectPermission)
            - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupProjectPermissions)
            - User is an admin for the organisation the project belongs to
        """
        user_permission_query = Q()
        group_permission_query = Q()
        for permission in permissions:
            user_permission_query = user_permission_query & Q(
                userpermission__permissions__key=permission
            )
            group_permission_query = group_permission_query & Q(
                grouppermission__permissions__key=permission
            )

        user_query = Q(userpermission__user=self) & (
            user_permission_query | Q(userpermission__admin=True)
        )
        group_query = Q(grouppermission__group__users=self) & (
            group_permission_query | Q(grouppermission__admin=True)
        )
        organisation_query = Q(
            organisation__userorganisation__user=self,
            organisation__userorganisation__role=OrganisationRole.ADMIN.name,
        )

        query = user_query | group_query | organisation_query

        return Project.objects.filter(query).distinct()

    def has_project_permission(self, permission, project):
        if self.is_project_admin(project):
            return True

        return project in self.get_permitted_projects([permission])

    def has_environment_permission(self, permission, environment):
        if self.is_project_admin(environment.project):
            return True

        return self._is_environment_admin_or_has_permission(environment, permission)

    def _is_environment_admin_or_has_permission(
        self, environment: Environment, permission_key: str = None
    ) -> bool:
        permission_query = Q(permissions__key=permission_key) | Q(admin=True)
        return (
            UserEnvironmentPermission.objects.filter(
                Q(environment=environment, user=self) & permission_query
            ).exists()
            or UserPermissionGroupEnvironmentPermission.objects.filter(
                Q(environment=environment, group__users=self) & permission_query
            ).exists()
        )

    def is_project_admin(self, project, allow_org_admin: bool = True):
        return (
            (allow_org_admin and self.is_organisation_admin(project.organisation))
            or UserProjectPermission.objects.filter(
                admin=True, user=self, project=project
            ).exists()
            or UserPermissionGroupProjectPermission.objects.filter(
                group__users=self, admin=True, project=project
            ).exists()
        )

    def get_permitted_environments(
        self, permission_key: str, project: Project
    ) -> QuerySet[Environment]:
        """
        Get all environments that the user has the given permissions for.

        Rules:
            - User has the required permissions directly (UserEnvironmentPermission)
            - User is in a UserPermissionGroup that has required permissions (UserPermissionGroupEnvironmentPermissions)
            - User is an admin for the project the environment belongs to
            - User is an admin for the organisation the environment belongs to
        """

        if self.is_project_admin(project):
            return project.environments.all()

        permission_groups = self.permission_groups.all()
        user_query = Q(userpermission__user=self) & (
            Q(userpermission__permissions__key=permission_key)
            | Q(userpermission__admin=True)
        )
        group_query = Q(grouppermission__group__in=permission_groups) & (
            Q(grouppermission__permissions__key=permission_key)
            | Q(grouppermission__admin=True)
        )

        return Environment.objects.filter(
            Q(project=project) & Q(user_query | group_query)
        ).distinct()

    @staticmethod
    def send_alert_to_admin_users(subject, message):
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=FFAdminUser._get_admin_user_emails(),
            fail_silently=True,
        )

    @classmethod
    def send_organisation_over_limit_alert(cls, organisation):
        subscription = getattr(organisation, "subscription", None)

        cls.send_alert_to_admin_users(
            subject="Organisation over number of seats",
            message="Organisation %s has used %d seats which is over their plan limit of %d "
            "(plan: %s)"
            % (
                str(organisation.name),
                organisation.num_seats,
                organisation.subscription.max_seats if subscription else 0,
                organisation.subscription.plan if subscription else "Free",
            ),
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
        allow_project_admin: bool = True,
        allow_organisation_admin: bool = True,
    ):
        return (
            (
                allow_organisation_admin
                and self.is_organisation_admin(environment.project.organisation)
            )
            or (
                allow_project_admin
                and self.is_project_admin(environment.project, allow_org_admin=False)
            )
            or UserEnvironmentPermission.objects.filter(
                admin=True, user=self, environment=environment
            ).exists()
            or UserPermissionGroupEnvironmentPermission.objects.filter(
                group__users=self, admin=True, environment=environment
            ).exists()
        )

    def has_organisation_permission(
        self, organisation: Organisation, permission_key: str
    ) -> bool:
        if self.is_organisation_admin(organisation):
            return True

        return (
            UserOrganisationPermission.objects.filter(
                user=self, organisation=organisation, permissions__key=permission_key
            ).exists()
            or UserPermissionGroupOrganisationPermission.objects.filter(
                group__users=self,
                organisation=organisation,
                permissions__key=permission_key,
            ).exists()
        )

    def get_permission_keys_for_organisation(
        self, organisation: Organisation
    ) -> typing.Iterable[str]:
        user_permission = UserOrganisationPermission.objects.filter(
            user=self, organisation=organisation
        ).first()
        group_permissions = UserPermissionGroupOrganisationPermission.objects.filter(
            group__users=self, organisation=organisation
        )

        all_permission_keys = set()
        for organisation_permission in [user_permission, *group_permissions]:
            if organisation_permission is not None:
                all_permission_keys.update(
                    {
                        permission.key
                        for permission in organisation_permission.permissions.all()
                    }
                )

        return all_permission_keys


class UserPermissionGroup(models.Model):
    """
    Model to group users within an organisation for the purposes of permissioning.
    """

    name = models.CharField(max_length=200)
    users = models.ManyToManyField(
        "users.FFAdminUser", related_name="permission_groups"
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="permission_groups"
    )

    class Meta:
        ordering = ("id",)  # explicit ordering to prevent pagination warnings

    def add_users_by_id(self, user_ids: list):
        users_to_add = []
        for user_id in user_ids:
            try:
                user = FFAdminUser.objects.get(
                    id=user_id, organisations=self.organisation
                )
            except FFAdminUser.DoesNotExist:
                # re-raise exception with useful error message
                raise FFAdminUser.DoesNotExist(
                    "User %d does not exist in this organisation" % user_id
                )
            users_to_add.append(user)
        self.users.add(*users_to_add)

    def remove_users_by_id(self, user_ids: list):
        self.users.remove(*user_ids)
