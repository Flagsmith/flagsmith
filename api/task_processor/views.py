from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from task_processor.serializers import MonitoringSerializer
from task_processor.statistics import get_task_queue_statistics


@swagger_auto_schema(method="GET", responses={200: MonitoringSerializer()})
@api_view(http_method_names=["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def monitoring(request, **kwargs):
    statistics = get_task_queue_statistics()
    serializer = MonitoringSerializer(instance=statistics)
    return Response(data=serializer.data, content_type="application/json")
