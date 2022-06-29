from core.helpers import get_current_site_url
from core.models import AbstractBaseExportableModel
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.template.loader import get_template
from django.utils import timezone

from app.utils import create_hash
from organisations.models import Organisation, OrganisationRole
from users.models import FFAdminUser


class AbstractBaseInviteModel(models.Model):
    hash = models.CharField(max_length=100, default=create_hash, unique=True)
    date_created = models.DateTimeField("DateCreated", auto_now_add=True)
    organisation = models.ForeignKey(Organisation, on_delete=models.CASCADE)
    role = models.CharField(
        choices=OrganisationRole.choices,
        max_length=50,
        default=OrganisationRole.USER,
    )

    class Meta:
        abstract = True


class InviteLink(AbstractBaseInviteModel, AbstractBaseExportableModel):
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Datetime that the invite link will cease to be active. "
        "Leave blank to enable indefinitely.",
    )

    @property
    def is_expired(self):
        return self.expires_at is not None and timezone.now() > self.expires_at


class Invite(AbstractBaseInviteModel):
    email = models.EmailField()
    invited_by = models.ForeignKey(
        FFAdminUser, related_name="sent_invites", null=True, on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("email", "organisation")
        ordering = ["organisation", "date_created"]
        # reference existing table after moving to own app to avoid db inconsistencies
        db_table = "users_invite"

    def save(self, *args, **kwargs):
        # send email invite before saving invite
        self.send_invite_mail()
        super(Invite, self).save(*args, **kwargs)

    def get_invite_uri(self):
        return f"{get_current_site_url()}/invite/{str(self.hash)}"

    def send_invite_mail(self):
        context = {
            "org_name": self.organisation.name,
            "invite_url": self.get_invite_uri(),
        }

        html_template = get_template("users/invite_to_org.html")
        plaintext_template = get_template("users/invite_to_org.txt")

        if self.invited_by:
            invited_by_name = self.invited_by.get_full_name()
            if not invited_by_name:
                invited_by_name = "A user"
            subject = settings.EMAIL_CONFIGURATION.get("INVITE_SUBJECT_WITH_NAME") % (
                invited_by_name,
                self.organisation.name,
            )
        else:
            subject = (
                settings.EMAIL_CONFIGURATION.get("INVITE_SUBJECT_WITHOUT_NAME")
                % self.organisation.name
            )

        to = self.email

        text_content = plaintext_template.render(context)
        html_content = html_template.render(context)
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.EMAIL_CONFIGURATION.get("INVITE_FROM_EMAIL"),
            [to],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

    def __str__(self):
        return "%s %s" % (self.email, self.organisation.name)
