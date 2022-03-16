import typing

from django.conf import settings
from django.db import models
from django.utils import timezone

from features.models import FeatureState
from features.workflows.exceptions import ChangeRequestNotApprovedError

if typing.TYPE_CHECKING:
    from users.models import FFAdminUser


class ChangeRequest(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    from_feature_state = models.ForeignKey(
        "features.FeatureState",
        on_delete=models.CASCADE,
        related_name="outbound_change_requests",
    )
    to_feature_state = models.ForeignKey(
        "features.FeatureState",
        on_delete=models.CASCADE,
        related_name="inbound_change_requests",
    )

    deleted_at = models.DateTimeField(null=True)
    committed_at = models.DateTimeField(null=True)

    def approve(self, user: "FFAdminUser"):
        # TODO: tests
        ChangeRequestApproval.objects.update_or_create(
            approved_at=timezone.now(), defaults={"change_request": self, "user": user}
        )

    def commit(self):
        # TODO: tests
        required_approvals = self.approvals.filter(required=True)
        if not all(approval.approved_at for approval in required_approvals):
            raise ChangeRequestNotApprovedError(
                "Change request has not been approved by all required approvers."
            )

        if not all(
            getattr(self.to_feature_state, attr)
            == getattr(self.from_feature_state, attr)
            for attr in ("environment", "feature", "feature_segment", "identity")
        ):
            raise RuntimeError(
                "Cannot commit change request: to_feature_state is not valid."
            )

        if not self.to_feature_state.live_from:
            self.to_feature_state.live_from = timezone.now()

        self.to_feature_state.version = FeatureState.get_next_version_number(
            environment_id=self.to_feature_state.environment_id,
            feature_id=self.to_feature_state.feature_id,
            feature_segment_id=self.to_feature_state.feature_segment_id,
            identity_id=self.to_feature_state.identity_id,
        )
        self.to_feature_state.save()

        self.committed_at = timezone.now()
        self.save()


class ChangeRequestApproval(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    change_request = models.ForeignKey(
        ChangeRequest, on_delete=models.CASCADE, related_name="approvals"
    )
    required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True)


class ChangeRequestComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    change_request = models.ForeignKey(
        ChangeRequest, on_delete=models.CASCADE, related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    body = models.TextField()
