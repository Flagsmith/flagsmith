import typing

from django.conf import settings
from django.db import models
from django.utils import timezone
from django_lifecycle import LifecycleModel

from features.models import FeatureState
from features.workflows.exceptions import ChangeRequestNotApprovedError

if typing.TYPE_CHECKING:
    from users.models import FFAdminUser


class ChangeRequest(LifecycleModel):
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
        ChangeRequestApproval.objects.update_or_create(
            change_request=self, user=user, defaults={"approved_at": timezone.now()}
        )

    def commit(self, committed_by: "FFAdminUser"):
        if not self.is_approved():
            raise ChangeRequestNotApprovedError(
                "Change request has not been approved by all required approvers."
            )

        feature_states = list(self.feature_states.all())

        for feature_state in feature_states:
            if not feature_state.live_from:
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

    def is_approved(self):
        return self.environment.minimum_change_request_approvals is not None and (
            self.approvals.filter(approved_at__isnull=False).count()
            >= self.environment.minimum_change_request_approvals
        )

    @property
    def is_committed(self):
        return self.committed_at is not None


class ChangeRequestApproval(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    change_request = models.ForeignKey(
        ChangeRequest, on_delete=models.CASCADE, related_name="approvals"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = ("user", "change_request")
