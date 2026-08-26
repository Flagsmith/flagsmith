from typing import TYPE_CHECKING, Any

import structlog
from common.environments.permissions import VIEW_IDENTITIES
from common.projects.permissions import VIEW_PROJECT
from django.db import models
from django.db.models import Prefetch
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.response import Response

from app.pagination import CustomPagination
from cohorts.models import Cohort
from core.dataclasses import AuthorData
from core.exceptions import ChangeRequestsEnabledError
from edge_api.identities.models import EdgeIdentity
from environments.identities.models import Identity
from environments.models import Environment
from features.models import FeatureState
from features.serializers import (
    AssociatedFeaturesQuerySerializer,
    SegmentAssociatedFeatureStateSerializer,
)
from features.versioning.models import EnvironmentFeatureVersion
from projects.models import Project
from segment_membership.metrics import (
    flagsmith_segment_membership_read_duration_seconds,
)
from segment_membership.services import (
    enqueue_membership_refresh,
    get_segment_members_page,
    is_membership_enabled,
)

from .models import Segment
from .permissions import SegmentPermissions
from .serializers import (
    CloneSegmentSerializer,
    SegmentListQuerySerializer,
    SegmentMembersQuerySerializer,
    SegmentMembersResponseSerializer,
    SegmentSerializer,
)
from .services import delete_segment, get_overrides_in_effect

if TYPE_CHECKING:
    from users.models import FFAdminUser

logger = structlog.get_logger("segments")


@method_decorator(
    name="list",
    decorator=extend_schema(
        tags=["mcp"],
        parameters=[SegmentListQuerySerializer],
        operation_id="list_project_segments",
        description="Retrieves all user segments defined for audience targeting within the project.",
    ),
)
@method_decorator(
    name="create",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="create_project_segment",
        description="Creates a new user segment for audience targeting within the project.",
    ),
)
@method_decorator(
    name="retrieve",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="get_project_segment",
        description="Retrieves detailed information about a specific user segment.",
    ),
)
@method_decorator(
    name="update",
    decorator=extend_schema(
        tags=["mcp"],
        operation_id="update_project_segment",
        description="Updates an existing user segment's properties and rules.",
    ),
)
class SegmentViewSet(viewsets.ModelViewSet):  # type: ignore[type-arg]
    serializer_class = SegmentSerializer
    permission_classes = [SegmentPermissions]
    pagination_class = CustomPagination

    def get_project(self) -> Project:
        user: "FFAdminUser" = self.request.user  # type: ignore[assignment]
        projects = user.get_permitted_projects(permission_key=VIEW_PROJECT)
        return get_object_or_404(projects, pk=self.kwargs["project_pk"])

    def get_queryset(self):  # type: ignore[no-untyped-def]
        if getattr(self, "swagger_fake_view", False):
            return Segment.objects.none()

        project = self.get_project()
        queryset = Segment.live_objects.filter(
            project=project, is_system_segment=False
        ).annotate(
            has_overrides=models.Exists(
                get_overrides_in_effect().filter(segment_id=models.OuterRef("pk"))
            )
        )

        if self.action == "list":
            # TODO: at the moment, the UI only shows the name and description of the segment in the list view.
            #  we shouldn't return all of the rules and conditions in the list view.
            queryset = queryset.prefetch_related(
                Prefetch(
                    "cohorts", queryset=Cohort.objects.select_related("environment")
                ),
                "membership_counts",
                "rules",
                "rules__conditions",
                "rules__rules",
                "rules__rules__conditions",
                "rules__rules__rules",
                "metadata",
            )

        query_serializer = SegmentListQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)

        identity_pk = query_serializer.validated_data.get("identity")
        if identity_pk:
            if identity_pk.isdigit():
                identity = Identity.objects.get(pk=identity_pk)
                segment_ids = [segment.id for segment in identity.get_segments()]
            else:
                segment_ids = EdgeIdentity.dynamo_wrapper.get_segment_ids(identity_pk)
            queryset = queryset.filter(id__in=segment_ids)

        search_term = query_serializer.validated_data.get("q")
        if search_term:
            queryset = queryset.filter(name__icontains=search_term)

        include_feature_specific = query_serializer.validated_data[
            "include_feature_specific"
        ]
        if include_feature_specific is False:
            queryset = queryset.filter(feature__isnull=True)

        return queryset

    @extend_schema(parameters=[AssociatedFeaturesQuerySerializer])
    @action(
        detail=True,
        methods=["GET"],
        url_path="associated-features",
        serializer_class=SegmentAssociatedFeatureStateSerializer,
    )
    def associated_features(self, request, *args, **kwargs):  # type: ignore[no-untyped-def]
        segment = self.get_object()

        query_serializer = AssociatedFeaturesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        filter_kwargs = {"feature_segment__segment": segment}
        if environment_id := query_serializer.validated_data.get("environment"):
            environment = Environment.objects.get(pk=environment_id)
            filter_kwargs["environment"] = environment
            if environment.use_v2_feature_versioning:
                filter_kwargs["environment_feature_version__in"] = (
                    EnvironmentFeatureVersion.objects.get_latest_versions_by_environment_id(
                        environment_id
                    )
                )

        queryset = FeatureState.objects.filter(**filter_kwargs)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[SegmentMembersQuerySerializer],
        responses={200: SegmentMembersResponseSerializer},
    )
    @action(detail=True, methods=["GET"], url_path="members")
    def members(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user: "FFAdminUser" = request.user  # type: ignore[assignment]
        project = self.get_project()
        # Fetch by pk directly rather than via get_object()/get_queryset(): the
        # latter applies the list endpoint's `q` (segment-name search), which
        # would filter this segment out when `q` is used here to search members.
        segment = get_object_or_404(
            Segment.live_objects.filter(project=project, is_system_segment=False),
            pk=self.kwargs["pk"],
        )
        self.check_object_permissions(request, segment)
        if not is_membership_enabled(project.organisation):
            raise NotFound()

        query_serializer = SegmentMembersQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        environment = get_object_or_404(
            Environment.objects.filter(project=project),
            pk=query_serializer.validated_data["environment"],
        )
        if not user.has_environment_permission(VIEW_IDENTITIES, environment):
            raise PermissionDenied()

        limit = query_serializer.validated_data["limit"]
        cursor = query_serializer.validated_data.get("cursor")
        q = query_serializer.validated_data.get("q")
        with flagsmith_segment_membership_read_duration_seconds.time():
            # Fetch one extra row to detect whether a further page exists, so the
            # last page doesn't advertise a phantom (empty) next page.
            members = get_segment_members_page(
                segment, environment, cursor=cursor, limit=limit + 1, q=q
            )

        has_more = len(members) > limit
        members = members[:limit]
        next_cursor = members[-1]["identifier"] if has_more else None
        return Response({"results": members, "next_cursor": next_cursor})

    def check_object_permissions(self, request: Request, obj: Segment) -> None:
        super().check_object_permissions(request, obj)
        if (
            self.action in ("update", "partial_update", "destroy", "clone")
            and obj.cohorts.exists()
        ):
            raise PermissionDenied(
                "This segment is managed by a cohort and cannot be edited "
                "or cloned directly."
            )
        if self.action in ("update", "partial_update"):
            self._check_change_requests_disabled(obj)

    def _check_change_requests_disabled(self, segment: Segment) -> None:
        """Refuse to edit a segment that can only be changed by a change request."""
        if not segment.project.is_workflow_enabled:
            return
        api_error = ChangeRequestsEnabledError(
            "Cannot update segments in a project with change requests enabled."
        )
        logger.warning(
            "update_rejected",
            organisation__id=segment.project.organisation_id,
            project__id=segment.project_id,
            segment__id=segment.id,
            reason=api_error.default_code,
        )
        raise api_error

    def _check_segment_is_deletable(self, segment: Segment) -> None:
        """
        Refuse to delete an overridden segment where change requests are enabled.

        Deleting a segment deletes the overrides pointing at it, which changes
        what the SDKs serve without anyone reviewing the change.
        """
        if not segment.project.is_workflow_enabled:
            return
        if not get_overrides_in_effect().filter(segment=segment).exists():
            return
        api_error = ChangeRequestsEnabledError(
            "Cannot delete a segment with feature overrides in a project with "
            "change requests enabled. Remove the overrides first."
        )
        logger.warning(
            "delete_rejected",
            organisation__id=segment.project.organisation_id,
            project__id=segment.project_id,
            segment__id=segment.id,
            reason=api_error.default_code,
        )
        raise api_error

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        segment = self.get_object()
        self._check_segment_is_deletable(segment)
        author = AuthorData.from_request(request)
        delete_segment(segment, author=author)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        request=CloneSegmentSerializer,
        responses={201: SegmentSerializer},
    )
    @action(
        detail=True,
        methods=["POST"],
        url_path="clone",
        serializer_class=CloneSegmentSerializer,
    )
    def clone(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        source_segment = self.get_object()
        serializer = CloneSegmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        clone = source_segment.clone(name=serializer.validated_data["name"])
        enqueue_membership_refresh(clone.project)
        return Response(SegmentSerializer(clone).data, status=status.HTTP_201_CREATED)


@extend_schema(responses={200: SegmentSerializer})
@api_view(["GET"])
def get_segment_by_uuid(request, uuid):  # type: ignore[no-untyped-def]
    accessible_projects = request.user.get_permitted_projects(VIEW_PROJECT)
    qs = Segment.live_objects.filter(project__in=accessible_projects)
    segment = get_object_or_404(qs, uuid=uuid)
    serializer = SegmentSerializer(instance=segment)
    return Response(serializer.data)
