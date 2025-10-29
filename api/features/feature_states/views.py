from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from environments.models import Environment
from features.models import Feature
from features.serializers import UpdateFlagSerializer


@api_view(http_method_names=["POST"])
def update_flag(request: Request, environment_id: int, feature_name: str) -> Response:
    environment = Environment.objects.get(id=environment_id)
    feature = Feature.objects.get(name=feature_name, project_id=environment.project_id)

    serializer = UpdateFlagSerializer(
        data=request.data, context={"request": request, "view": update_flag}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save(environment=environment, feature=feature)

    return Response(serializer.data, status=status.HTTP_200_OK)
