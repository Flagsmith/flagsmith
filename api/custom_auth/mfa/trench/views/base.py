from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from custom_auth.mfa.trench.command.activate_mfa_method import (
    activate_mfa_method_command,
)
from custom_auth.mfa.trench.command.create_mfa_method import (
    create_mfa_method_command,
)
from custom_auth.mfa.trench.command.deactivate_mfa_method import (
    deactivate_mfa_method_command,
)
from custom_auth.mfa.trench.exceptions import MFAValidationError
from custom_auth.mfa.trench.models import MFAMethod
from custom_auth.mfa.trench.responses import ErrorResponse
from custom_auth.mfa.trench.serializers import (
    MFAMethodActivationConfirmationValidator,
    UserMFAMethodSerializer,
)
from custom_auth.mfa.trench.utils import get_mfa_handler

User: AbstractUser = get_user_model()


class MFAMethodActivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        if method != "app":
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            user = request.user
            mfa = create_mfa_method_command(
                user_id=user.id,
                name=method,
            )
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)
        return get_mfa_handler(mfa_method=mfa).dispatch_message()


class MFAMethodConfirmActivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        serializer = MFAMethodActivationConfirmationValidator(
            mfa_method_name=method, user=request.user, data=request.data
        )
        if not serializer.is_valid():
            return Response(status=HTTP_400_BAD_REQUEST, data=serializer.errors)
        backup_codes = activate_mfa_method_command(
            user_id=request.user.id,
            name=method,
            code=serializer.validated_data["code"],
        )
        return Response({"backup_codes": backup_codes})


class MFAMethodDeactivationView(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request: Request, method: str) -> Response:
        try:
            deactivate_mfa_method_command(
                mfa_method_name=method, user_id=request.user.id
            )
            return Response(status=HTTP_204_NO_CONTENT)
        except MFAValidationError as cause:
            return ErrorResponse(error=cause)


class ListUserActiveMFAMethods(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        active_mfa_methods = MFAMethod.objects.filter(user=request.user, is_active=True)
        serializer = UserMFAMethodSerializer(active_mfa_methods, many=True)
        return Response(serializer.data)
