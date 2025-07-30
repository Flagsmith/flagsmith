import logging
import typing
import uuid

from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from django.db.models import Count, QuerySet
from django.utils import timezone
from django_lifecycle import (  # type: ignore[import-untyped]
    AFTER_SAVE,
    LifecycleModel,
    hook,
)
from django_lifecycle.conditions import (  # type: ignore[import-untyped]
    WhenFieldHasChanged,
)
from pydantic import BaseModel

from organisations.models import (
    Organisation,
    OrganisationRole,
    UserOrganisation,
)
from organisations.subscriptions.exceptions import (
    SubscriptionDoesNotSupportSeatUpgrade,
)
from permissions.permission_service import (
    get_permitted_environments_for_user,
    get_permitted_projects_for_user,
    is_user_environment_admin,
    is_user_organisation_admin,
    is_user_project_admin,
    user_has_organisation_permission,
)
from projects.models import Project
from users.abc import UserABC
from users.auth_type import AuthType
from users.constants import DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE
from users.exceptions import InvalidInviteError


class UTMDataModel(BaseModel):
    utm_source: typing.Optional[str] = None
    utm_medium: typing.Optional[str] = None
    utm_campaign: typing.Optional[str] = None
    utm_term: typing.Optional[str] = None
    utm_content: typing.Optional[str] = None


if typing.TYPE_CHECKING:
    from environments.models import Environment
    from organisations.invites.models import (
        AbstractBaseInviteModel,
        Invite,
        InviteLink,
    )

logger = logging.getLogger(__name__)


class SignUpType(models.TextChoices):
    NO_INVITE = "NO_INVITE"
    INVITE_EMAIL = "INVITE_EMAIL"
    INVITE_LINK = "INVITE_LINK"


class UserManager(BaseUserManager):  # type: ignore[type-arg]
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):  # type: ignore[no-untyped-def]
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):  # type: ignore[no-untyped-def]
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)  # type: ignore[no-untyped-call]

    def create_superuser(self, email, password, **extra_fields):  # type: ignore[no-untyped-def]
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)  # type: ignore[no-untyped-call]

    def get_by_natural_key(self, email):  # type: ignore[no-untyped-def]
        # Used to allow case insensitive login
        return self.get(email__iexact=email)


class FFAdminUser(LifecycleModel, AbstractUser):  # type: ignore[django-manager-missing,misc]
    organisations = models.ManyToManyField(
        Organisation, related_name="users", blank=True, through=UserOrganisation
    )
    email = models.EmailField(unique=True, null=False)
    objects = UserManager()  # type: ignore[assignment,misc]
    username = models.CharField(unique=True, max_length=150, null=True, blank=True)  # type: ignore[misc]
    first_name = models.CharField("first name", max_length=150)
    last_name = models.CharField("last name", max_length=150)
    google_user_id = models.CharField(max_length=50, null=True, blank=True)
    github_user_id = models.CharField(max_length=50, null=True, blank=True)
    onboarding_data = models.TextField(blank=True, null=True)
    # Default to True, since it is covered in our Terms of Service.
    marketing_consent_given = models.BooleanField(
        default=True,
        help_text="Determines whether the user has agreed to receive marketing mails",
    )

    sign_up_type = models.CharField(
        choices=SignUpType.choices, max_length=100, blank=True, null=True
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    USERNAME_FIELD = "username" if settings.LDAP_ENABLED else "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "sign_up_type"]

    class Meta:
        ordering = ["id"]
        verbose_name = "Feature flag admin user"

    def __str__(self):  # type: ignore[no-untyped-def]
        return self.email

    @property
    def superuser(self) -> bool:
        return self.is_staff and self.is_superuser

    @superuser.setter
    def superuser(self, value: bool) -> None:
        self.is_staff = value
        self.is_superuser = value

    @hook(AFTER_SAVE, condition=(WhenFieldHasChanged("email", has_changed=True)))  # type: ignore[misc]
    def send_warning_email(self) -> None:
        from users.tasks import send_email_changed_notification_email

        send_email_changed_notification_email.delay(
            args=(
                self.first_name,
                settings.DEFAULT_FROM_EMAIL,
                self.initial_value("email"),
            )
        )

    def delete_orphan_organisations(self) -> None:
        Organisation.objects.filter(
            id__in=self.organisations.values_list("id", flat=True)
        ).annotate(users_count=Count("users")).filter(users_count=1).delete()

    def delete(  # type: ignore[no-untyped-def,override]
        self,
        delete_orphan_organisations: bool = DEFAULT_DELETE_ORPHAN_ORGANISATIONS_VALUE,
    ):
        if delete_orphan_organisations:
            self.delete_orphan_organisations()
        super().delete()

    def set_password(self, raw_password):  # type: ignore[no-untyped-def]
        super().set_password(raw_password)
        if self.id:
            self.password_reset_requests.all().delete()

    @property
    def auth_type(self):  # type: ignore[no-untyped-def]
        if self.google_user_id:
            return AuthType.GOOGLE.value

        if self.github_user_id:
            return AuthType.GITHUB.value

        return AuthType.EMAIL.value

    @property
    def full_name(self):  # type: ignore[no-untyped-def]
        return self.get_full_name()  # type: ignore[no-untyped-call]

    @property
    def email_domain(self):  # type: ignore[no-untyped-def]
        return self.email.split("@")[1]

    def get_full_name(self):  # type: ignore[no-untyped-def]
        if not self.first_name:
            return None
        return " ".join([self.first_name, self.last_name]).strip()

    def can_send_password_reset_email(self) -> bool:
        limit = timezone.now() - timezone.timedelta(  # type: ignore[attr-defined]
            seconds=settings.PASSWORD_RESET_EMAIL_COOLDOWN
        )
        return (
            self.password_reset_requests.filter(requested_at__gte=limit).count()
            < settings.MAX_PASSWORD_RESET_EMAILS
        )

    def join_organisation_from_invite_email(self, invite_email: "Invite"):  # type: ignore[no-untyped-def]
        if invite_email.email.lower() != self.email.lower():
            raise InvalidInviteError("Registered email does not match invited email")
        self.join_organisation_from_invite(invite_email)
        self.permission_groups.add(*invite_email.permission_groups.all())
        invite_email.delete()

    def join_organisation_from_invite_link(self, invite_link: "InviteLink"):  # type: ignore[no-untyped-def]
        self.join_organisation_from_invite(invite_link)

    def join_organisation_from_invite(self, invite: "AbstractBaseInviteModel"):  # type: ignore[no-untyped-def]
        organisation = invite.organisation

        if settings.ENABLE_CHARGEBEE and organisation.over_plan_seats_limit(
            additional_seats=1
        ):
            if organisation.is_auto_seat_upgrade_available():
                organisation.subscription.add_single_seat()  # type: ignore[no-untyped-call]
            else:
                raise SubscriptionDoesNotSupportSeatUpgrade()

        self.add_organisation(organisation, role=OrganisationRole(invite.role))  # type: ignore[no-untyped-call]

    def is_organisation_admin(self, organisation: typing.Union["Organisation", int]):  # type: ignore[no-untyped-def]
        return is_user_organisation_admin(self, organisation)

    def get_admin_organisations(self):  # type: ignore[no-untyped-def]
        return Organisation.objects.filter(
            userorganisation__user=self,
            userorganisation__role=OrganisationRole.ADMIN.name,
        )

    def add_organisation(self, organisation, role=OrganisationRole.USER):  # type: ignore[no-untyped-def]
        UserOrganisation.objects.create(
            user=self, organisation=organisation, role=role.name
        )
        default_groups = organisation.permission_groups.filter(is_default=True)
        self.permission_groups.add(*default_groups)

    def remove_organisation(self, organisation):  # type: ignore[no-untyped-def]
        UserOrganisation.objects.filter(user=self, organisation=organisation).delete()
        self.project_permissions.filter(project__organisation=organisation).delete()
        self.environment_permissions.filter(
            environment__project__organisation=organisation
        ).delete()
        self.permission_groups.remove(*organisation.permission_groups.all())

    def get_organisation_role(self, organisation):  # type: ignore[no-untyped-def]
        user_organisation = self.get_user_organisation(organisation)
        if user_organisation:
            return user_organisation.role

    def get_organisation_join_date(self, organisation):  # type: ignore[no-untyped-def]
        user_organisation = self.get_user_organisation(organisation)
        if user_organisation:
            return user_organisation.date_joined

    def get_user_organisation(  # type: ignore[return]
        self, organisation: typing.Union["Organisation", int]
    ) -> UserOrganisation:
        organisation_id = getattr(organisation, "id", organisation)

        try:
            # Since the user list view relies on this data, we prefetch it in
            # the queryset, hence we can't use `userorganisation_set.get()`
            # and instead use this next(filter()) approach. Since most users
            # won't have more than ~1 organisation, we can accept the performance
            # hit in the case that we are only getting the organisation for a
            # single user.
            return next(
                filter(
                    lambda uo: uo.organisation_id == organisation_id,
                    self.userorganisation_set.all(),
                )
            )
        except StopIteration:
            logger.warning(
                "User %d is not part of organisation %d" % (self.id, organisation_id)
            )

    def get_permitted_projects(
        self,
        permission_key: str,
        tag_ids: typing.List[int] = None,  # type: ignore[assignment]
    ) -> QuerySet[Project]:
        return get_permitted_projects_for_user(self, permission_key, tag_ids)

    def has_project_permission(
        self,
        permission: str,
        project: Project,
        tag_ids: typing.List[int] = None,  # type: ignore[assignment]
    ) -> bool:
        if self.is_project_admin(project):
            return True
        return project in self.get_permitted_projects(permission, tag_ids=tag_ids)

    def has_environment_permission(
        self,
        permission: str,
        environment: "Environment",
        tag_ids: typing.List[int] = None,  # type: ignore[assignment]
    ) -> bool:
        return environment in self.get_permitted_environments(
            permission, environment.project, tag_ids=tag_ids
        )

    def is_project_admin(self, project: Project) -> bool:
        return is_user_project_admin(self, project)

    def get_permitted_environments(
        self,
        permission_key: str,
        project: Project,
        tag_ids: typing.List[int] = None,  # type: ignore[assignment]
        prefetch_metadata: bool = False,
    ) -> QuerySet["Environment"]:
        return get_permitted_environments_for_user(
            self, project, permission_key, tag_ids, prefetch_metadata=prefetch_metadata
        )

    @staticmethod
    def send_alert_to_admin_users(subject, message):  # type: ignore[no-untyped-def]
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=FFAdminUser._get_admin_user_emails(),  # type: ignore[no-untyped-call]
            fail_silently=True,
        )

    @staticmethod
    def _get_admin_user_emails():  # type: ignore[no-untyped-def]
        return [
            user["email"]
            for user in FFAdminUser.objects.filter(is_staff=True).values("email")
        ]

    def belongs_to(self, organisation_id: int) -> bool:
        return self.userorganisation_set.filter(
            organisation_id=organisation_id
        ).exists()

    def is_environment_admin(
        self,
        environment: "Environment",
    ) -> bool:
        return is_user_environment_admin(self, environment)

    def has_organisation_permission(
        self, organisation: Organisation, permission_key: str
    ) -> bool:
        return user_has_organisation_permission(self, organisation, permission_key)

    def add_to_group(
        self, group: "UserPermissionGroup", group_admin: bool = False
    ) -> None:
        UserPermissionGroupMembership.objects.create(
            ffadminuser=self, userpermissiongroup=group, group_admin=group_admin
        )

    def is_group_admin(self, group_id) -> bool:  # type: ignore[no-untyped-def]
        return UserPermissionGroupMembership.objects.filter(
            ffadminuser=self, userpermissiongroup__id=group_id, group_admin=True
        ).exists()

    def make_group_admin(self, group_id: int):  # type: ignore[no-untyped-def]
        UserPermissionGroupMembership.objects.filter(
            ffadminuser=self, userpermissiongroup__id=group_id
        ).update(group_admin=True)

    def remove_as_group_admin(self, group_id: int):  # type: ignore[no-untyped-def]
        UserPermissionGroupMembership.objects.filter(
            ffadminuser=self, userpermissiongroup__id=group_id
        ).update(group_admin=False)


# Since we can't enforce FFAdminUser to implement the  UserABC interface using inheritance
# we use __subclasshook__[1] method on UserABC to check if FFAdminUser implements the required interface
# [1]https://docs.python.org/3/library/abc.html#abc.ABCMeta.__subclasshook__
assert issubclass(FFAdminUser, UserABC)


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
        through_fields=["userpermissiongroup", "ffadminuser"],  # type: ignore[arg-type]
    )
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="permission_groups"
    )
    ldap_dn = models.CharField(blank=True, null=True, unique=True, max_length=255)
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

    def add_users_by_id(self, user_ids: list):  # type: ignore[no-untyped-def,type-arg]
        users_to_add = list(
            FFAdminUser.objects.filter(id__in=user_ids, organisations=self.organisation)
        )
        if len(user_ids) != len(users_to_add):
            missing_ids = set(users_to_add).difference({u.id for u in users_to_add})
            raise FFAdminUser.DoesNotExist(
                "Users %s do not exist in this organisation" % ", ".join(missing_ids)
            )
        self.users.add(*users_to_add)

    def remove_users_by_id(self, user_ids: list):  # type: ignore[no-untyped-def,type-arg]
        self.users.remove(*user_ids)


class HubspotLead(models.Model):
    user = models.OneToOneField(
        FFAdminUser,
        related_name="hubspot_lead",
        on_delete=models.CASCADE,
    )
    hubspot_id = models.CharField(unique=True, max_length=100, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class HubspotTrackerUTMData(typing.TypedDict, total=False):
    utm_source: str
    utm_medium: str
    utm_campaign: str
    utm_term: str
    utm_content: str


class HubspotTracker(models.Model):
    user = models.OneToOneField(
        FFAdminUser,
        related_name="hubspot_tracker",
        on_delete=models.CASCADE,
    )
    hubspot_cookie = models.CharField(
        unique=True,
        max_length=100,
        null=True,
        blank=True,
    )
    utm_data: HubspotTrackerUTMData = models.JSONField(
        default=None, blank=True, null=True
    )  # type: ignore[assignment]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
