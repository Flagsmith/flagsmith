from django.db.models import QuerySet
from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from cohorts import services
from cohorts.models import Cohort
from cohorts.permissions import CohortPermission, CohortPlanPermission
from cohorts.serializers import CohortSerializer
from environments.views import NestedEnvironmentViewSet
from projects.exceptions import DynamoNotEnabledError


class CohortViewSet(
    NestedEnvironmentViewSet[Cohort],
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
):
    serializer_class = CohortSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, CohortPlanPermission, CohortPermission]
    model_class = Cohort
    lookup_field = "id"
    lookup_url_kwarg = "cohort_id"

    def initial(self, request: Request, *args: object, **kwargs: object) -> None:
        super().initial(request, *args, **kwargs)
        # Cohorts only sync to edge identities for now; core (Postgres
        # identities) support comes later.
        if not services.edge_sync_enabled(self._get_environment().project):
            raise DynamoNotEnabledError()

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

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        services.delete_cohort(self.get_object())
        return Response(status=status.HTTP_202_ACCEPTED)
