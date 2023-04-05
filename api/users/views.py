from contextlib import suppress

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.sites.shortcuts import get_current_site
from django.db.models import QuerySet
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.edit import FormView
from drf_yasg2.utils import swagger_auto_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from organisations.models import Organisation
from organisations.permissions.permissions import (
    MANAGE_USER_GROUPS,
    NestedIsOrganisationAdminPermission,
    OrganisationUsersPermission,
    UserPermissionGroupPermission,
)
from organisations.serializers import UserOrganisationSerializer
from users.models import (
    FFAdminUser,
    UserPermissionGroup,
    UserPermissionGroupMembership,
)
from users.serializers import (
    ListUsersQuerySerializer,
    UserIdsSerializer,
    UserListSerializer,
    UserPermissionGroupSerializerDetail,
)

from .forms import InitConfigForm


class InitialConfigurationView(PermissionRequiredMixin, FormView):
    template_name = "users/onboard.html"
    form_class = InitConfigForm
    permission_denied_message = (
        "FAILED TO INIT Configuration. USER(S) ALREADY EXIST IN SYSTEM."
    )

    def has_permission(self):
        return FFAdminUser.objects.count() == 0

    def handle_no_permission(self):
        raise Http404("CAN NOT INIT CONFIGURATION. USER(S) ALREADY EXIST IN SYSTEM.")

    def form_valid(self, form):
        form.create_admin()
        form.update_site()
        return HttpResponse("INSTALLATION CONFIGURED SUCCESSFULLY")


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


@method_decorator(
    decorator=swagger_auto_schema(query_serializer=ListUsersQuerySerializer()),
    name="list",
)
class FFAdminUserViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, OrganisationUsersPermission)
    pagination_class = None

    def get_queryset(self):
        if self.kwargs.get("organisation_pk"):
            queryset = FFAdminUser.objects.filter(
                organisations__id=self.kwargs.get("organisation_pk")
            )
            queryset = self._apply_query_filters(queryset)
            return queryset
        else:
            return FFAdminUser.objects.none()

    def _apply_query_filters(self, queryset: QuerySet):
        serializer = ListUsersQuerySerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        filter_data = serializer.data

        if filter_data.get("exclude_current"):
            queryset = queryset.exclude(id=self.request.user.id)

        return queryset

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
        organisation = Organisation.objects.get(id=organisation_pk)

        qs = UserPermissionGroup.objects.filter(organisation=organisation)
        if not self.request.user.has_organisation_permission(
            organisation, MANAGE_USER_GROUPS
        ):
            qs = qs.filter(
                userpermissiongroupmembership__ffadminuser=self.request.user,
                userpermissiongroupmembership__group_admin=True,
            )

        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.detail is True:
            with suppress(ValueError):
                context["group_admins"] = UserPermissionGroupMembership.objects.filter(
                    userpermissiongroup__id=int(self.kwargs["pk"]), group_admin=True
                ).values_list("ffadminuser__id", flat=True)
        return context

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
        user_ids = request.data["user_ids"]

        if request.user.id in user_ids and not request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            raise PermissionDenied("Non-admin users cannot add themselves to a group.")

        try:
            group.add_users_by_id(user_ids)
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
        user_ids = request.data["user_ids"]

        if request.user.id in user_ids and not request.user.is_organisation_admin(
            Organisation.objects.get(pk=organisation_pk)
        ):
            raise PermissionDenied(
                "Non-admin users cannot remove themselves from a group."
            )

        group.remove_users_by_id(user_ids)
        return Response(UserPermissionGroupSerializerDetail(instance=group).data)


@permission_classes([IsAuthenticated(), NestedIsOrganisationAdminPermission()])
@api_view(["POST"])
def make_user_group_admin(
    request: Request, organisation_pk: int, group_pk: int, user_pk: int
):
    user = get_object_or_404(
        FFAdminUser,
        userorganisation__organisation_id=organisation_pk,
        permission_groups__id=group_pk,
        id=user_pk,
    )
    user.make_group_admin(group_pk)
    return Response()


@permission_classes([IsAuthenticated(), NestedIsOrganisationAdminPermission()])
@api_view(["POST"])
def remove_user_as_group_admin(
    request: Request, organisation_pk: int, group_pk: int, user_pk: int
):
    user = get_object_or_404(
        FFAdminUser,
        userorganisation__organisation_id=organisation_pk,
        permission_groups__id=group_pk,
        id=user_pk,
    )
    user.remove_as_group_admin(group_pk)
    return Response()
