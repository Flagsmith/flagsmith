from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from platform_hub import services
from platform_hub.serializers import (
    DaysQuerySerializer,
    IntegrationBreakdownSerializer,
    OrganisationMetricsSerializer,
    ReleasePipelineOverviewSerializer,
    StaleFlagsPerProjectSerializer,
    SummarySerializer,
    UsageTrendSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary_view(request: Request) -> Response:
    query_serializer = DaysQuerySerializer(data=request.query_params)
    query_serializer.is_valid(raise_exception=True)
    days: int = query_serializer.validated_data["days"]

    organisations = request.user.get_admin_organisations()  # type: ignore[union-attr]
    data = services.get_summary(organisations, days=days)
    serializer = SummarySerializer(data)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def organisations_view(request: Request) -> Response:
    organisations = request.user.get_admin_organisations()  # type: ignore[union-attr]
    data = services.get_organisation_metrics(organisations)
    serializer = OrganisationMetricsSerializer(data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def usage_trends_view(request: Request) -> Response:
    query_serializer = DaysQuerySerializer(data=request.query_params)
    query_serializer.is_valid(raise_exception=True)
    days: int = query_serializer.validated_data["days"]

    organisations = request.user.get_admin_organisations()  # type: ignore[union-attr]
    data = services.get_usage_trends(organisations, days=days)
    serializer = UsageTrendSerializer(data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stale_flags_view(request: Request) -> Response:
    organisations = request.user.get_admin_organisations()  # type: ignore[union-attr]
    data = services.get_stale_flags_per_project(organisations)
    serializer = StaleFlagsPerProjectSerializer(data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def integrations_view(request: Request) -> Response:
    organisations = request.user.get_admin_organisations()  # type: ignore[union-attr]
    data = services.get_integration_breakdown(organisations)
    serializer = IntegrationBreakdownSerializer(data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def release_pipelines_view(request: Request) -> Response:
    organisations = request.user.get_admin_organisations()  # type: ignore[union-attr]
    data = services.get_release_pipeline_stats(organisations)
    serializer = ReleasePipelineOverviewSerializer(data, many=True)
    return Response(serializer.data)
