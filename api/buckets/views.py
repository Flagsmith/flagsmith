from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets

from app.pagination import CustomPagination
from buckets.models import Bucket
from buckets.permissions import BucketPermissions, VIEW_BUCKET
from buckets.serializers import (
    BucketQuerySerializer,
    BucketSerializer,
    CreateBucketSerializer,
    UpdateBucketSerializer,
)
from projects.models import Project


class BucketViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Buckets within a Project.

    Buckets are used to organize Features into logical groups within a project.
    Each bucket belongs to a single project, and features can optionally belong
    to one bucket.
    """

    permission_classes = [BucketPermissions]
    pagination_class = CustomPagination
    lookup_field = "id"

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        return {
            "list": BucketSerializer,
            "retrieve": BucketSerializer,
            "create": CreateBucketSerializer,
            "update": UpdateBucketSerializer,
            "partial_update": UpdateBucketSerializer,
        }.get(self.action, BucketSerializer)

    def get_queryset(self):
        """
        Get buckets for the project specified in URL.
        Apply search and sorting from query parameters.
        Annotate with feature_count for better performance.
        """
        if getattr(self, "swagger_fake_view", False):
            return Bucket.objects.none()

        # Get project and verify user has access
        accessible_projects = self.request.user.get_permitted_projects(VIEW_BUCKET)
        project = get_object_or_404(accessible_projects, pk=self.kwargs["project_pk"])

        # Base queryset with feature count annotation for performance
        queryset = Bucket.objects.filter(project=project).annotate(
            feature_count=Count("features")
        )

        # Apply query parameters
        query_serializer = BucketQuerySerializer(data=self.request.query_params)
        query_serializer.is_valid(raise_exception=True)
        query_data = query_serializer.validated_data

        # Search filter
        if search := query_data.get("search"):
            queryset = queryset.filter(name__icontains=search)

        # Sorting
        sort_prefix = "-" if query_data["sort_direction"] == "DESC" else ""
        queryset = queryset.order_by(f"{sort_prefix}{query_data['sort_field']}")

        return queryset

    def get_serializer_context(self):
        """Add project to serializer context"""
        context = super().get_serializer_context()
        if getattr(self, "swagger_fake_view", False):
            return context

        project = get_object_or_404(
            Project.objects.all(), pk=self.kwargs["project_pk"]
        )
        context.update(project=project, user=self.request.user)
        return context

    def perform_create(self, serializer):
        """Create bucket with project from URL"""
        serializer.save(project_id=int(self.kwargs.get("project_pk")))

    def perform_update(self, serializer):
        """Update bucket (project cannot be changed)"""
        serializer.save()

    @swagger_auto_schema(query_serializer=BucketQuerySerializer())
    def list(self, request, *args, **kwargs):
        """
        List all buckets in the project.

        Query parameters:
        - search: Filter by bucket name (case-insensitive contains)
        - sort_field: "created_date" or "name" (default: "created_date")
        - sort_direction: "ASC" or "DESC" (default: "ASC")
        """
        return super().list(request, *args, **kwargs)
