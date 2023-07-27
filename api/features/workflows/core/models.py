import importlib
import logging
import typing

from core.helpers import get_current_site_url
from core.models import (
    AbstractBaseExportableModel,
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory,
)
from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django_lifecycle import (
    AFTER_CREATE,
    AFTER_SAVE,
    AFTER_UPDATE,
    LifecycleModel,
    LifecycleModelMixin,
    hook,
)

from audit.constants import (
    CHANGE_REQUEST_APPROVED_MESSAGE,
    CHANGE_REQUEST_COMMITTED_MESSAGE,
    CHANGE_REQUEST_CREATED_MESSAGE,
    CHANGE_REQUEST_DELETED_MESSAGE,
)
from audit.related_object_type import RelatedObjectType
from audit.tasks import (
    create_feature_state_updated_by_change_request_audit_log,
    create_feature_state_went_live_audit_log,
)
from features.models import FeatureState

from .exceptions import (
    CannotApproveOwnChangeRequest,
    ChangeRequestNotApprovedError,
)

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from projects.models import Project
    from users.models import FFAdminUser

logger = logging.getLogger(__name__)


class ChangeRequest(
    LifecycleModelMixin,
    SoftDeleteExportableModel,
    abstract_base_auditable_model_factory(["uuid"]),
):
    related_object_type = RelatedObjectType.CHANGE_REQUEST
    history_record_class_path = "features.workflows.core.models.HistoricalChangeRequest"

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="change_requests",
    )

    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="change_requests",
    )

    deleted_at = models.DateTimeField(null=True)
    committed_at = models.DateTimeField(null=True)
    committed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="committed_change_requests",
        null=True,
    )

    def approve(self, user: "FFAdminUser"):
        if user.id == self.user_id:
            raise CannotApproveOwnChangeRequest(
                "User cannot approve their own Change Request."
            )

        ChangeRequestApproval.objects.update_or_create(
            change_request=self, user=user, defaults={"approved_at": timezone.now()}
        )

    def commit(self, committed_by: "FFAdminUser"):
        if not self.is_approved():
            raise ChangeRequestNotApprovedError(
                "Change request has not been approved by all required approvers."
            )

        logger.debug("Committing change request #%d", self.id)

        feature_states = list(self.feature_states.all())

        for feature_state in feature_states:
            if not feature_state.live_from or feature_state.live_from < timezone.now():
                feature_state.live_from = timezone.now()

            feature_state.version = FeatureState.get_next_version_number(
                environment_id=feature_state.environment_id,
                feature_id=feature_state.feature_id,
                feature_segment_id=feature_state.feature_segment_id,
                identity_id=feature_state.identity_id,
            )

        FeatureState.objects.bulk_update(
            feature_states, fields=["live_from", "version"]
        )

        self.committed_at = timezone.now()
        self.committed_by = committed_by
        self.save()

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        return CHANGE_REQUEST_CREATED_MESSAGE % self.title

    def get_delete_log_message(self, history_instance) -> typing.Optional[str]:
        return CHANGE_REQUEST_DELETED_MESSAGE % self.title

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        if (
            history_instance.prev_record
            and history_instance.prev_record.committed_at is None
            and self.committed_at is not None
        ):
            return CHANGE_REQUEST_COMMITTED_MESSAGE % self.title

    def get_audit_log_author(self, history_instance) -> typing.Optional["FFAdminUser"]:
        if history_instance.history_type == "+":
            return self.user
        elif history_instance.history_type == "~" and (
            history_instance.prev_record
            and history_instance.prev_record.committed_at is None
            and self.committed_at is not None
        ):
            return self.committed_by

    def _get_environment(self) -> typing.Optional["Environment"]:
        return self.environment

    def _get_project(self) -> typing.Optional["Project"]:
        return self.environment.project

    def is_approved(self):
        return self.environment.minimum_change_request_approvals is None or (
            self.approvals.filter(approved_at__isnull=False).count()
            >= self.environment.minimum_change_request_approvals
        )

    @property
    def is_committed(self):
        return self.committed_at is not None

    @property
    def url(self):
        if not self.id:
            raise AttributeError(
                "Change request must be saved before it has a url attribute."
            )
        url = get_current_site_url()
        url += f"/project/{self.environment.project_id}"
        url += f"/environment/{self.environment.api_key}"
        url += f"/change-requests/{self.id}"
        return url

    @property
    def email_subject(self):
        return f"Flagsmith Change Request: {self.title} (#{self.id})"

    @hook(AFTER_CREATE, when="committed_at", is_not=None)
    @hook(AFTER_SAVE, when="committed_at", was=None, is_not=None)
    def create_audit_log_for_related_feature_state(self):
        for feature_state in self.feature_states.all():
            if self.committed_at < feature_state.live_from:
                create_feature_state_went_live_audit_log.delay(
                    delay_until=feature_state.live_from, args=(feature_state.id,)
                )
            else:
                create_feature_state_updated_by_change_request_audit_log.delay(
                    args=(feature_state.id,)
                )


class ChangeRequestApproval(LifecycleModel, abstract_base_auditable_model_factory()):
    related_object_type = RelatedObjectType.CHANGE_REQUEST
    history_record_class_path = (
        "features.workflows.core.models.HistoricalChangeRequestApproval"
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    change_request = models.ForeignKey(
        ChangeRequest, on_delete=models.CASCADE, related_name="approvals"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ("user", "change_request")

    @hook(AFTER_CREATE, when="approved_at", is_now=None)
    def send_email_notification_to_assignee(self):
        context = {
            "url": self.change_request.url,
            "approver": self.user,
            "author": self.change_request.user,
        }

        send_mail(
            subject=self.change_request.email_subject,
            message=render_to_string(
                "workflows_core/change_request_assignee_notification.txt", context
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.user.email],
            html_message=render_to_string(
                "workflows_core/change_request_assignee_notification.html", context
            ),
            fail_silently=True,
        )

    @hook(AFTER_CREATE, when="approved_at", is_not=None)
    @hook(AFTER_UPDATE, when="approved_at", was=None, is_not=None)
    def send_email_notification_to_author(self):
        context = {
            "url": self.change_request.url,
            "approver": self.user,
            "author": self.change_request.user,
        }

        send_mail(
            subject=self.change_request.email_subject,
            message=render_to_string(
                "workflows_core/change_request_approved_author_notification.txt",
                context,
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.change_request.user.email],
            html_message=render_to_string(
                "workflows_core/change_request_approved_author_notification.html",
                context,
            ),
            fail_silently=True,
        )

    def get_create_log_message(self, history_instance) -> typing.Optional[str]:
        if self.approved_at is not None:
            return CHANGE_REQUEST_APPROVED_MESSAGE % self.change_request.title

    def get_update_log_message(self, history_instance) -> typing.Optional[str]:
        if (
            history_instance.prev_record.approved_at is None
            and self.approved_at is not None
        ):
            return CHANGE_REQUEST_APPROVED_MESSAGE % self.change_request.title

    def get_audit_log_related_object_id(self, history_instance) -> int:
        return self.change_request_id

    def get_audit_log_author(self, history_instance) -> "FFAdminUser":
        return self.user

    def _get_environment(self):
        return self.change_request.environment


class ChangeRequestGroupAssignment(AbstractBaseExportableModel, LifecycleModel):
    change_request = models.ForeignKey(
        ChangeRequest, on_delete=models.CASCADE, related_name="group_assignments"
    )
    group = models.ForeignKey("users.UserPermissionGroup", on_delete=models.CASCADE)

    @hook(AFTER_SAVE)
    def notify_group(self):
        if settings.WORKFLOWS_LOGIC_INSTALLED:
            workflows_tasks = importlib.import_module(
                f"{settings.WORKFLOWS_LOGIC_MODULE_PATH}.tasks"
            )
            workflows_tasks.notify_group_of_change_request_assignment.delay(
                kwargs={"change_request_group_assignment_id": self.id}
            )
