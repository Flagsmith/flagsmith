from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views import View
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from organisations.models import Organisation
from organisations.permissions import (
    OrganisationUsersPermission,
    UserPermissionGroupPermission,
)
from organisations.serializers import (
    UserOrganisationSerializer,
)
from users.models import FFAdminUser, UserPermissionGroup
from users.serializers import (
    UserIdsSerializer,
    UserListSerializer,
    UserPermissionGroupSerializerDetail,
)


class AdminInitView(View):
    def get(self, request):
        if FFAdminUser.objects.count() == 0:
            admin = FFAdminUser.objects.create_superuser(
                settings.ADMIN_EMAIL,
                settings.ADMIN_INITIAL_PASSWORD,
                is_active=True,
            )
            admin.save()
            return HttpResponse("ADMIN USER CREATED")
        else:
            return HttpResponse(
                "FAILED TO INIT ADMIN USER. USER(S) ALREADY EXIST IN SYSTEM."
            )


class FFAdminUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, OrganisationUsersPermission)
    pagination_class = None

    def get_queryset(self):
        if self.kwargs.get("organisation_pk"):
            return FFAdminUser.objects.filter(
                organisations__id=self.kwargs.get("organisation_pk")
            )
        else:
            return FFAdminUser.objects.none()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "update_role":
            return UserOrganisationSerializer

        return UserListSerializer

    def get_serializer_context(self):
        context = super(FFAdminUserViewSet, self).get_serializer_context()
        if self.kwargs.get("organisation_pk"):
            context["organisation"] = Organisation.objects.get(
                pk=self.kwargs.get("organisation_pk")
            )
        return context

    @action(detail=True, methods=["POST"], url_path="update-role")
    def update_role(self, request, organisation_pk, pk):
        user = self.get_object()
        organisation = Organisation.objects.get(pk=organisation_pk)
        user_organisation = user.get_user_organisation(organisation)

        serializer = self.get_serializer(
            instance=user_organisation, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            UserListSerializer(user, context={"organisation": organisation}).data
        )


def password_reset_redirect(request, uidb64, token):
    protocol = "https" if request.is_secure() else "https"
    current_site = get_current_site(request)
    domain = current_site.domain
    return redirect(
        protocol + "://" + domain + "/password-reset/" + uidb64 + "/" + token
    )


class UserPermissionGroupViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, UserPermissionGroupPermission]
    serializer_class = UserPermissionGroupSerializerDetail

    def get_queryset(self):
        organisation_pk = self.kwargs.get("organisation_pk")
        return UserPermissionGroup.objects.filter(organisation__pk=organisation_pk)

    def perform_create(self, serializer):
        serializer.save(organisation_id=self.kwargs["organisation_pk"])

    def perform_update(self, serializer):
        serializer.save(organisation_id=self.kwargs["organisation_pk"])

    @swagger_auto_schema(
        request_body=UserIdsSerializer,
        responses={200: UserPermissionGroupSerializerDetail},
    )
    @action(detail=True, methods=["POST"], url_path="add-users")
    def add_users(self, request, organisation_pk, pk):
        group = self.get_object()
        try:
            group.add_users_by_id(request.data["user_ids"])
        except FFAdminUser.DoesNotExist as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(UserPermissionGroupSerializerDetail(instance=group).data)

    @swagger_auto_schema(
        request_body=UserIdsSerializer,
        responses={200: UserPermissionGroupSerializerDetail},
    )
    @action(detail=True, methods=["POST"], url_path="remove-users")
    def remove_users(self, request, organisation_pk, pk):
        group = self.get_object()
        group.remove_users_by_id(request.data["user_ids"])
        return Response(UserPermissionGroupSerializerDetail(instance=group).data)
