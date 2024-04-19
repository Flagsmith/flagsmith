import importlib
import logging
import typing
from datetime import datetime

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
    BEFORE_DELETE,
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
from environments.tasks import rebuild_environment_document
from features.models import FeatureState
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.tasks import trigger_update_version_webhooks
from features.workflows.core.exceptions import (
    CannotApproveOwnChangeRequest,
    ChangeRequestDeletionError,
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

    # We allow null here so that deleting users does not cascade to deleting change
    # requests which can be used for historical purposes.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="change_requests",
        null=True,
    )

    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="change_requests",
    )

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

        self._publish_feature_states()
        self._publish_environment_feature_versions(committed_by)

        self.committed_at = timezone.now()
        self.committed_by = committed_by
        self.save()

    def _publish_feature_states(self) -> None:
        now = timezone.now()

        if feature_states := list(self.feature_states.all()):
            for feature_state in feature_states:
                if not feature_state.live_from or feature_state.live_from < now:
                    feature_state.live_from = now

                feature_state.version = FeatureState.get_next_version_number(
                    environment_id=feature_state.environment_id,
                    feature_id=feature_state.feature_id,
                    feature_segment_id=feature_state.feature_segment_id,
                    identity_id=feature_state.identity_id,
                )

            FeatureState.objects.bulk_update(
                feature_states, fields=["live_from", "version"]
            )

    def _publish_environment_feature_versions(
        self, published_by: "FFAdminUser"
    ) -> None:
        now = timezone.now()

        if environment_feature_versions := list(
            self.environment_feature_versions.all()
        ):
            for environment_feature_version in environment_feature_versions:
                if (
                    not environment_feature_version.live_from
                    or environment_feature_version.live_from < now
                ):
                    environment_feature_version.live_from = now

                environment_feature_version.publish(published_by, persist=False)

            EnvironmentFeatureVersion.objects.bulk_update(
                environment_feature_versions,
                fields=["published_at", "published_by", "live_from"],
            )

            for environment_feature_version in environment_feature_versions:
                trigger_update_version_webhooks.delay(
                    kwargs={
                        "environment_feature_version_uuid": str(
                            environment_feature_version.uuid
                        )
                    },
                    delay_until=environment_feature_version.live_from,
                )
                rebuild_environment_document.delay(
                    kwargs={"environment_id": self.environment_id},
                    delay_until=environment_feature_version.live_from,
                )

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

    @hook(BEFORE_DELETE)
    def prevent_change_request_delete_if_committed(self) -> None:
        # In the workflows-logic module, we prevent change requests from being
        # deleted but, since this can have unexpected effects on published
        # feature states, we also want to prevent it at the ORM level.
        if self.committed_at and not (
            self.environment.deleted_at
            or (self._live_from and self._live_from > timezone.now())
        ):
            raise ChangeRequestDeletionError(
                "Cannot delete a Change Request that has been committed."
            )

    @property
    def _live_from(self) -> datetime | None:
        # First we check if there are feature states associated with the change request
        # and, if so, we return the live_from of the feature state with the earliest
        # live_from.
        if first_feature_state := self.feature_states.order_by("live_from").first():
            return first_feature_state.live_from

        # Then we do the same for environment feature versions. Note that a change request
        # can not have feature states and environment feature versions.
        elif first_environment_feature_version := self.environment_feature_versions.order_by(
            "live_from"
        ).first():
            return first_environment_feature_version.live_from

        return None


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
            workflows_tasks = importlib.import_module("workflows_logic.tasks")
            workflows_tasks.notify_group_of_change_request_assignment.delay(
                kwargs={"change_request_group_assignment_id": self.id}
            )
