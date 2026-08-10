import typing

from django.db.models import QuerySet
from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from cohorts import services
from cohorts.models import Cohort
from cohorts.permissions import CohortPermission
from cohorts.serializers import CohortSerializer
from environments.views import NestedEnvironmentViewSet

if typing.TYPE_CHECKING:
    from users.models import FFAdminUser


class CohortViewSet(
    NestedEnvironmentViewSet[Cohort],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    """Manage trait-synced cohorts for an environment."""

    serializer_class = CohortSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, CohortPermission]
    model_class = Cohort
    lookup_field = "id"
    lookup_url_kwarg = "cohort_id"

    def get_queryset(self) -> QuerySet[Cohort]:
        # A cohort awaiting drain-then-delete is already gone from the
        # user's point of view.
        return (
            super()
            .get_queryset()
            .filter(deletion_requested_at__isnull=True)
            .select_related("segment")
            .order_by("id")
        )

    def perform_create(self, serializer: BaseSerializer[Cohort]) -> None:
        serializer.save(
            environment=self._get_environment(),
            user=self._get_user(self.request),
        )

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        services.delete_cohort(self.get_object(), self._get_user(request))
        return Response(status=status.HTTP_202_ACCEPTED)

    @staticmethod
    def _get_user(request: Request) -> "FFAdminUser":
        return request.user  # type: ignore[return-value]
