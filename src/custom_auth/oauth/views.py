from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from custom_auth.oauth.serializers import OAuthAccessTokenSerializer
from custom_auth.serializers import CustomTokenSerializer


@swagger_auto_schema(method="post", request_body=OAuthAccessTokenSerializer, responses={200: CustomTokenSerializer})
@api_view(["POST"])
@permission_classes([AllowAny])
def login_with_google(request):
    serializer = OAuthAccessTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.save()
    return Response(data=CustomTokenSerializer(instance=token).data)
