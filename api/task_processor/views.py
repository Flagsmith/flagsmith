from django.db.models import Count, Q
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from task_processor.models import Task, TaskResult
from task_processor.serializers import MonitoringSerializer


@api_view(http_method_names=["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
@swagger_auto_schema(responses={200: MonitoringSerializer()})
def monitoring(request, **kwargs):
    qs = Task.objects.annotate(num_task_runs=Count("task_runs")).aggregate(
        waiting=Count("id", filter=Q(num_task_runs=0)),
        completed=Count(
            "id",
            filter=Q(task_runs__result=TaskResult.SUCCESS),
        ),
        failed=Count("id", filter=Q(num_failures__gte=3)),
    )
    serializer = MonitoringSerializer(instance=qs)
    return Response(data=serializer.data, headers={"Content-Type": "application/json"})
